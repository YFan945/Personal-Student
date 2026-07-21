from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "workflow_guard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_guard", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HookDecisionTests(unittest.TestCase):
    """PreToolUse hook 决策逻辑测试"""

    def test_blocks_production_without_confirmation(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict("os.environ", {}, clear=True):
                decision = module.hook_decision(
                    {
                        "tool_name": "Bash",
                        "cwd": tmp,
                        "tool_input": {
                            "command": "python slide_spec_to_pptx_brief.py spec.yaml"
                        },
                    }
                )
        self.assertIsNotNone(decision)
        self.assertEqual(
            "deny",
            decision["hookSpecificOutput"]["permissionDecision"],
        )

    def test_allows_after_confirmation(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "outputs" / ".student-presentation-state.json"
            state_path.parent.mkdir()
            summary = Path(tmp) / "summary.md"
            summary.write_text("confirmed", encoding="utf-8")
            state_path.write_text(
                json.dumps({
                    "state": "intake_confirmed",
                    "summary_file": str(summary),
                    "summary_sha256": module.sha256_file(summary),
                }), encoding="utf-8"
            )
            with mock.patch.dict("os.environ", {}, clear=True):
                decision = module.hook_decision(
                    {
                        "tool_name": "Bash",
                        "cwd": tmp,
                        "tool_input": {
                            "command": "node run_with_pptxgenjs.js deck.js"
                        },
                    }
                )
        self.assertIsNone(decision)

    def test_allows_in_producing_state(self) -> None:
        """producing 状态应允许生产命令"""
        module = load_module()
        for state in ("planned", "producing", "qa"):
            with self.subTest(state=state):
                with tempfile.TemporaryDirectory() as tmp:
                    state_path = (
                        Path(tmp) / "outputs" / ".student-presentation-state.json"
                    )
                    state_path.parent.mkdir()
                    summary = Path(tmp) / "summary.md"
                    summary.write_text("confirmed", encoding="utf-8")
                    state_path.write_text(
                        json.dumps({
                            "state": state,
                            "summary_file": str(summary),
                            "summary_sha256": module.sha256_file(summary),
                        }), encoding="utf-8"
                    )
                    with mock.patch.dict("os.environ", {}, clear=True):
                        decision = module.hook_decision(
                            {
                                "tool_name": "Bash",
                                "cwd": tmp,
                                "tool_input": {
                                    "command": "python build_support_outputs.py spec --json"
                                },
                            }
                        )
                self.assertIsNone(decision)

    def test_blocks_in_complete_state(self) -> None:
        """complete 状态不应再允许生产命令"""
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "outputs" / ".student-presentation-state.json"
            state_path.parent.mkdir()
            state_path.write_text(
                json.dumps({"state": "complete"}), encoding="utf-8"
            )
            with mock.patch.dict("os.environ", {}, clear=True):
                decision = module.hook_decision(
                    {
                        "tool_name": "Bash",
                        "cwd": tmp,
                        "tool_input": {
                            "command": "node run_with_pptxgenjs.js deck.js"
                        },
                    }
                )
        self.assertIsNotNone(decision)
        self.assertEqual(
            "deny",
            decision["hookSpecificOutput"]["permissionDecision"],
        )

    def test_missing_summary_hash_blocks_production(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "outputs" / ".student-presentation-state.json"
            state_path.parent.mkdir()
            state_path.write_text(json.dumps({"state": "intake_confirmed"}), encoding="utf-8")
            with mock.patch.dict("os.environ", {}, clear=True):
                decision = module.hook_decision({
                    "tool_name": "Bash", "cwd": tmp,
                    "tool_input": {"command": "node run_with_pptxgenjs.js deck.js"},
                })
        self.assertIsNotNone(decision)

    def test_ignores_unrelated_bash(self) -> None:
        module = load_module()
        for cmd in ("git status", "npm install", "ls -la", "echo hello"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(
                    module.hook_decision(
                        {"tool_name": "Bash", "tool_input": {"command": cmd}}
                    )
                )

    def test_ignores_non_bash_tool(self) -> None:
        module = load_module()
        self.assertIsNone(
            module.hook_decision(
                {
                    "tool_name": "Read",
                    "tool_input": {
                        "command": "python slide_spec_to_pptx_brief.py x.yaml"
                    },
                }
            )
        )

    def test_blocked_state_does_not_allow_more_production(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "outputs" / ".student-presentation-state.json"
            state_path.parent.mkdir()
            state_path.write_text(
                json.dumps({"state": "blocked"}), encoding="utf-8"
            )
            with mock.patch.dict("os.environ", {}, clear=True):
                decision = module.hook_decision(
                    {
                        "tool_name": "Bash",
                        "cwd": tmp,
                        "tool_input": {
                            "command": "node run_with_pptxgenjs.js deck.js"
                        },
                    }
                )
        self.assertIsNotNone(decision)
        self.assertEqual(
            "deny",
            decision["hookSpecificOutput"]["permissionDecision"],
        )

    def test_incomplete_state_blocks_production(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "outputs" / ".student-presentation-state.json"
            state_path.parent.mkdir()
            state_path.write_text(
                json.dumps({"state": "incomplete"}), encoding="utf-8"
            )
            with mock.patch.dict("os.environ", {}, clear=True):
                decision = module.hook_decision(
                    {
                        "tool_name": "Bash",
                        "cwd": tmp,
                        "tool_input": {
                            "command": "python pptx_delivery_check.py --pptx x.pptx"
                        },
                    }
                )
        self.assertIsNotNone(decision)
        self.assertEqual(
            "deny",
            decision["hookSpecificOutput"]["permissionDecision"],
        )

    def test_no_false_positive_on_echo_comment(self) -> None:
        """echo/注释中包含脚本名不应被误拦截"""
        module = load_module()
        safe_commands = [
            "echo 'learned about run_with_pptxgenjs.js today'",
            "# TODO: use slide_spec_to_pptx_brief.py later",
            "cat build_support_outputs.py",
            "echo build_support_outputs.py",
        ]
        for cmd in safe_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNone(
                    module.hook_decision(
                        {"tool_name": "Bash", "tool_input": {"command": cmd}}
                    )
                )

    def test_claude_plugin_root_pattern_matches(self) -> None:
        """${CLAUDE_PLUGIN_ROOT} 前缀的脚本调用应被正确识别"""
        module = load_module()
        commands = [
            'python "${CLAUDE_PLUGIN_ROOT}/scripts/slide_spec_to_pptx_brief.py" spec.yaml',
            'node "${CLAUDE_PLUGIN_ROOT}/scripts/run_with_pptxgenjs.js" deck.js',
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                with tempfile.TemporaryDirectory() as tmp:
                    with mock.patch.dict("os.environ", {}, clear=True):
                        decision = module.hook_decision(
                            {
                                "tool_name": "Bash",
                                "cwd": tmp,
                                "tool_input": {"command": cmd},
                            }
                        )
                self.assertIsNotNone(decision)
                self.assertEqual(
                    "deny",
                    decision["hookSpecificOutput"]["permissionDecision"],
                )

    def test_empty_command_ignored(self) -> None:
        module = load_module()
        self.assertIsNone(
            module.hook_decision(
                {"tool_name": "Bash", "tool_input": {"command": ""}}
            )
        )


class StateTransitionTests(unittest.TestCase):
    """状态机转换规则测试"""

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

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
                self.assertFalse(
                    module.transition_allowed(seq[i], seq[i - 1])
                )

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
        for state in module.SEQUENCE:
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
                "visual_inspection": {"completed": True, "remaining_blockers": 0},
            }), encoding="utf-8")
            self.assertEqual([], module.validate_completion_manifest(manifest, pptx))
            manifest.write_text("{}", encoding="utf-8")
            self.assertTrue(module.validate_completion_manifest(manifest, pptx))


class FastPreScanTests(unittest.TestCase):
    """快速预扫描测试"""

    def test_skip_json_parsing_for_unrelated_input(self) -> None:
        """非生产命令应跳过 JSON 解析"""
        module = load_module()
        with mock.patch.object(sys.stdin.buffer, "read", return_value=b""):
            result = module._check_and_parse_stdin()
        # 无 stdin 输入时应返回 None
        self.assertIsNone(result)


class ProjectRootTests(unittest.TestCase):
    """project_root 一致性测试"""

    def test_uses_claude_project_dir(self) -> None:
        module = load_module()
        with mock.patch.dict(
            "os.environ", {"CLAUDE_PROJECT_DIR": "/fake/project"}, clear=True
        ):
            root = module.project_root()
            self.assertEqual(root, Path("/fake/project").resolve())

    def test_falls_back_to_cwd(self) -> None:
        module = load_module()
        with mock.patch.dict("os.environ", {}, clear=True):
            root = module.project_root()
            self.assertEqual(root, Path.cwd().resolve())


class ProductionPatternTests(unittest.TestCase):
    """生产命令模式匹配测试"""

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_matches_production_commands(self) -> None:
        commands = [
            "python slide_spec_to_pptx_brief.py spec.yaml",
            "python3 build_support_outputs.py --json",
            "node run_with_pptxgenjs.js deck.js",
            "python pptx_delivery_check.py --pptx x.pptx",
            "python create_revision_manifest.py old new --strict",
            "py slide_spec_to_pptx_brief.py spec.yaml",
            "python3.12 build_support_outputs.py --json",
            r"C:\Python312\python.exe slide_spec_to_pptx_brief.py spec.yaml",
            "uv run python slide_spec_to_pptx_brief.py spec.yaml",
        ]
        for cmd in commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(
                    self.module._contains_production_command(cmd),
                    f"应匹配生产命令: {cmd}",
                )

    def test_does_not_match_echo_comments(self) -> None:
        safe = [
            "echo 'using run_with_pptxgenjs.js later'",
            "echo build_support_outputs.py",
            "# slide_spec_to_pptx_brief.py is the bridge",
            "cat pptx_delivery_check.py",
            "ls create_revision_manifest.py",
            "python validate_slide_spec.py spec.yaml",
        ]
        for cmd in safe:
            with self.subTest(cmd=cmd):
                self.assertFalse(
                    self.module._contains_production_command(cmd),
                    f"不应匹配非调用命令: {cmd}",
                )

    def test_empty_command(self) -> None:
        self.assertFalse(self.module._contains_production_command(""))
        self.assertFalse(self.module._contains_production_command("   "))


if __name__ == "__main__":
    unittest.main()
