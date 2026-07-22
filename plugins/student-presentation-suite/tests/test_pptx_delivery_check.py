from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from PIL import Image

from test_helpers import load_module


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "student-presentation-ppt" / "scripts" / "pptx_delivery_check.py"


class PptxDeliveryCheckTests(unittest.TestCase):
    def write_minimal_pptx(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr(
                "ppt/slides/slide1.xml",
                """<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>""",
            )

    def write_valid_preview_and_manifest(self, pptx: Path, preview: Path, manifest: Path) -> None:
        image = Image.new("RGB", (640, 360), "white")
        image.paste("navy", (0, 0, 640, 80))
        image.save(preview)
        manifest.write_text(json.dumps({
            "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
            "slide_count": 1,
            "rendered_page_count": 1,
            "scenario_contract_passed": True,
            "preview_files": [preview.name],
            "preview_sha256": [hashlib.sha256(preview.read_bytes()).hexdigest()],
            "visual_inspection": {
                "completed": True, "inspected_pages": [1], "repair_cycles": 1,
                "remaining_blockers": 0,
            },
        }), encoding="utf-8")

    def test_derives_and_requires_notes_and_preview_by_default(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "demo-presentation.pptx"
            self.write_minimal_pptx(pptx)

            result = module.inspect_delivery(pptx, None, [])

        self.assertEqual(["notes", "preview"], result["missing_expected_files"])
        self.assertTrue(result["requirements"]["notes_required"])
        self.assertTrue(result["requirements"]["preview_required"])

    def test_explicit_exceptions_do_not_report_optional_files_missing(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "demo-presentation.pptx"
            self.write_minimal_pptx(pptx)

            result = module.inspect_delivery(
                pptx,
                None,
                [],
                require_notes=False,
                require_preview=False,
            )

        self.assertEqual([], result["missing_expected_files"])

    def test_font_inheritance_uncertainty_is_not_blocker_like(self) -> None:
        module = load_module(SCRIPT)
        result = module.summarize_static_risks(
            {
                "findings": [
                    {
                        "slide": 1,
                        "shape": 1,
                        "text_preview": "Inherited text",
                        "char_count": 14,
                        "min_font_pt": None,
                        "risk": ["font-size-not-explicit"],
                    }
                ]
            }
        )

        self.assertEqual(0, result["blocker_like_count"])

    def test_qa_manifest_binds_current_pptx_and_decodable_preview(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, preview, manifest = root / "demo-presentation.pptx", root / "demo-preview.png", root / "qa-manifest.json"
            notes = root / "demo-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            self.write_valid_preview_and_manifest(pptx, preview, manifest)
            result = module.inspect_delivery(pptx, notes, [preview], qa_manifest=manifest)
        self.assertTrue(result["ok"])
        self.assertTrue(result["qa_manifest"]["valid"])
        self.assertEqual("complete", result["delivery_report"]["status"])
        self.assertEqual("1/1", result["delivery_report"]["preview_page_coverage"])

    def test_corrupt_preview_fails_qa_manifest(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, preview, manifest = root / "demo-presentation.pptx", root / "demo-preview.png", root / "qa-manifest.json"
            notes = root / "demo-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            preview.write_text("not an image", encoding="utf-8")
            manifest.write_text("{}", encoding="utf-8")
            result = module.inspect_delivery(pptx, notes, [preview], qa_manifest=manifest)
        self.assertFalse(result["ok"])
        self.assertFalse(result["preview_validation"][0]["valid"])

    def test_blocked_on_static_scan_error(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, notes = root / "deck.pptx", root / "deck-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            preview = root / "deck-preview.png"
            self.write_valid_preview_and_manifest(pptx, preview, root / "qa-manifest.json")
            # 模拟静态扫描返回 error
            with mock.patch.object(module, "summarize_static_risks", return_value={"blocker_like_count": 0}):
                with mock.patch.object(module, "_load_inspect_pptx", return_value=lambda p: {"error": "模拟错误", "findings": []}):
                    result = module.inspect_delivery(pptx, notes, [preview], qa_manifest=root / "qa-manifest.json")
        self.assertFalse(result["ok"])

    def test_blocked_on_blocker_like_risk(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, notes = root / "deck.pptx", root / "deck-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            preview = root / "deck-preview.png"
            self.write_valid_preview_and_manifest(pptx, preview, root / "qa-manifest.json")
            with mock.patch.object(module, "summarize_static_risks", return_value={"blocker_like_count": 3}):
                result = module.inspect_delivery(pptx, notes, [preview], qa_manifest=root / "qa-manifest.json")
        self.assertFalse(result["ok"])

    def test_blocked_on_missing_qa_manifest(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, notes = root / "deck.pptx", root / "deck-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            result = module.inspect_delivery(pptx, notes, [], qa_manifest=None)
        self.assertFalse(result["ok"])
        self.assertFalse(result["qa_manifest"]["valid"])

    def test_blocked_on_pptx_unreadable(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "not-a-pptx.pptx"
            pptx.write_text("not a zip", encoding="utf-8")
            result = module.inspect_delivery(pptx, None, [])
        self.assertFalse(result["ok"])

    def test_blocked_on_style_report_failure(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, notes = root / "deck.pptx", root / "deck-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            preview = root / "deck-preview.png"
            self.write_valid_preview_and_manifest(pptx, preview, root / "qa-manifest.json")
            style_report = root / "style-report.json"
            style_report.write_text(json.dumps({"valid": False, "errors": ["style mismatch"]}), encoding="utf-8")
            result = module.inspect_delivery(pptx, notes, [preview], qa_manifest=root / "qa-manifest.json", style_report=style_report)
        self.assertFalse(result["ok"])

    def test_strict_mode_exits_on_failure(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "missing.pptx"
            with self.assertRaises(SystemExit):
                result = module.inspect_delivery(pptx, None, [])
                self.assertFalse(result["ok"])
                module.parse_args = lambda: mock.Mock(strict=True)
                if not result["ok"]:
                    raise SystemExit(1)
