from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliContractTests(unittest.TestCase):
    def test_all_published_python_clis_have_non_mutating_help(self) -> None:
        scripts = (
            "analyze_presentation_spec.py",
            "build_support_outputs.py",
            "bump_version.py",
            "check_claude_pptx_env.py",
            "check_plugin_release.py",
            "create_revision_manifest.py",
            "manage_versions.py",
            "pptx_tool.py",
            "scenario_render_matrix.py",
            "slide_spec_to_pptx_brief.py",
            "smoke_pptx.py",
            "validate_presentation_brief.py",
            "validate_slide_spec.py",
            "visual_system_smoke_gallery.py",
            "workflow_guard.py",
        )
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for name in scripts:
            with self.subTest(script=name):
                result = subprocess.run(
                    [sys.executable, "-B", str(ROOT / "scripts" / name), "--help"],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("usage:", result.stdout.lower())

    def test_node_generation_wrapper_has_help_contract(self) -> None:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "run_with_pptxgenjs.js"), "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
