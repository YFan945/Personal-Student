from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_helpers import load_module

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "workflow_guard.py"


class StateTransitionTests(unittest.TestCase):
    """状态机转换规则测试"""

    @classmethod
    def setUpClass(cls):
        cls.module = load_module(SCRIPT)

    def test_all_valid_forward_transitions(self) -> None:
        module = self.module
        seq = module.SEQUENCE
        for i in range(len(seq) - 1):
            with self.subTest(before=seq[i], after=seq[i + 1]):
                self.assertTrue(
                    module.transition_allowed(seq[i], seq[i + 1])
                )

    def test_reverse_transitions_blocked(self) -> None:
        module = self.module
        seq = module.SEQUENCE
        for i in range(1, len(seq)):
            with self.subTest(before=seq[i], after=seq[i - 1]):
                if (seq[i], seq[i - 1]) in module.REWORK_EDGES:
                    # qa → producing 是允许的返工边，用于修复后重建
                    self.assertTrue(module.transition_allowed(seq[i], seq[i - 1]))
                    continue
                self.assertFalse(
                    module.transition_allowed(seq[i], seq[i - 1])
                )

    def test_rework_edge_qa_to_producing_allowed(self) -> None:
        module = self.module
        self.assertTrue(module.transition_allowed("qa", "producing"))
        # 其他回退仍被拒绝
        self.assertFalse(module.transition_allowed("complete", "qa"))
        self.assertFalse(module.transition_allowed("producing", "planned"))

    def test_recovery_edge_incomplete_to_qa_allowed(self) -> None:
        module = self.module
        self.assertTrue(module.transition_allowed("incomplete", "qa"))
        # 其它从 incomplete 的出口仍被拒绝（除 reset）
        self.assertFalse(module.transition_allowed("incomplete", "planned"))
        self.assertFalse(module.transition_allowed("incomplete", "producing"))
        # 终态互转仍允许（complete→incomplete 等）
        self.assertTrue(module.transition_allowed("complete", "incomplete"))
        self.assertTrue(module.transition_allowed("incomplete", "blocked"))

    def test_skip_transitions_blocked(self) -> None:
        module = self.module
        self.assertFalse(module.transition_allowed("intake_pending", "producing"))
        self.assertFalse(module.transition_allowed("intake_confirmed", "qa"))
        self.assertFalse(module.transition_allowed("planned", "complete"))

    def test_terminal_from_intake_pending_blocked(self) -> None:
        module = self.module
        self.assertFalse(module.transition_allowed("intake_pending", "incomplete"))
        self.assertFalse(module.transition_allowed("intake_pending", "blocked"))

    def test_terminal_from_later_states_allowed(self) -> None:
        module = self.module
        for state in ("intake_confirmed", "planned", "producing", "qa", "complete"):
            for terminal in ("incomplete", "blocked"):
                with self.subTest(before=state, after=terminal):
                    self.assertTrue(
                        module.transition_allowed(state, terminal)
                    )

    def test_invalid_state_names(self) -> None:
        module = self.module
        self.assertFalse(module.transition_allowed("bogus", "planned"))
        self.assertFalse(module.transition_allowed("intake_pending", "bogus"))

    def test_same_state_blocked(self) -> None:
        module = self.module
        # SEQUENCE 内状态与终态（incomplete/blocked）的同状态自转都应被拒绝
        for state in list(module.SEQUENCE) + sorted(module.TERMINAL):
            with self.subTest(state=state):
                self.assertFalse(
                    module.transition_allowed(state, state)
                )

    def test_complete_requires_valid_qa_manifest(self) -> None:
        module = self.module
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "deck.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", "<slide/>")
            manifest = root / "qa.json"
            manifest.write_text(json.dumps({
                "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                "slide_count": 1,
                "rendered_page_count": 1,
                "scenario_contract_passed": True,
                "visual_inspection": {
                    "completed": True,
                    "remaining_blockers": 0,
                    "inspected_pages": [1],
                    "repair_cycles": 0,
                    "no_repair_needed_reason": "No visual defect was found.",
                },
            }), encoding="utf-8")
            delivery = root / "delivery.json"
            package = root / "package.json"
            package.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )
            delivery.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "status": "complete",
                        "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                        "qa_manifest_sha256": hashlib.sha256(
                            manifest.read_bytes()
                        ).hexdigest(),
                        "package_report_sha256": hashlib.sha256(
                            package.read_bytes()
                        ).hexdigest(),
                        "package_blockers": 0,
                        "package_validation_passed": True,
                        "preview_page_coverage": "1/1",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                module.validate_completion_manifest(manifest, pptx, delivery),
            )
            manifest.write_text("{}", encoding="utf-8")
            self.assertTrue(module.validate_completion_manifest(manifest, pptx))

    def test_complete_rejects_missing_manifest(self) -> None:
        module = self.module
        self.assertTrue(module.validate_completion_manifest(None, None))

    def test_complete_rejects_hash_mismatch(self) -> None:
        module = self.module
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "deck.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", "<slide/>")
            other = root / "other.pptx"
            with zipfile.ZipFile(other, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", "<slide><!-- different --></slide>")
            manifest = root / "qa.json"
            manifest.write_text(json.dumps({
                "pptx_sha256": hashlib.sha256(other.read_bytes()).hexdigest(),
                "slide_count": 1,
                "rendered_page_count": 1,
                "visual_inspection": {"completed": True, "remaining_blockers": 0},
            }), encoding="utf-8")
            errors = module.validate_completion_manifest(manifest, pptx)
            self.assertTrue(any("pptx_sha256" in e for e in errors))

    def test_complete_rejects_remaining_blockers(self) -> None:
        module = self.module
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "deck.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", "<slide/>")
            manifest = root / "qa.json"
            manifest.write_text(json.dumps({
                "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                "slide_count": 1,
                "rendered_page_count": 1,
                "visual_inspection": {"completed": True, "remaining_blockers": 2},
            }), encoding="utf-8")
            errors = module.validate_completion_manifest(manifest, pptx)
            self.assertTrue(any("blocker" in e.lower() for e in errors))

    def test_complete_allows_missing_visual_inspection(self) -> None:
        """视觉检查为可选：无 visual_inspection 的 manifest 在 delivery 通过时仍可 complete。"""
        module = self.module
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "deck.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", "<slide/>")
            manifest = root / "qa.json"
            manifest.write_text(json.dumps({
                "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                "slide_count": 1,
                "scenario_contract_passed": True,
            }), encoding="utf-8")
            delivery = root / "delivery.json"
            delivery.write_text(json.dumps({
                "ok": True,
                "status": "complete",
                "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                "qa_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                "package_blockers": 0,
                "package_validation_passed": True,
                "preview_page_coverage": "0/0",
            }), encoding="utf-8")
            self.assertEqual(
                [],
                module.validate_completion_manifest(manifest, pptx, delivery),
            )


class ProjectRootTests(unittest.TestCase):
    """project_root 一致性测试"""

    def test_uses_claude_project_dir(self) -> None:
        module = load_module(SCRIPT)
        with mock.patch.dict(
            "os.environ", {"CLAUDE_PROJECT_DIR": "/fake/project"}, clear=True
        ):
            root = module.project_root()
            self.assertEqual(root, Path("/fake/project").resolve())

    def test_falls_back_to_cwd(self) -> None:
        module = load_module(SCRIPT)
        with mock.patch.dict("os.environ", {}, clear=True):
            root = module.project_root()
            self.assertEqual(root, Path.cwd().resolve())


if __name__ == "__main__":
    unittest.main()
