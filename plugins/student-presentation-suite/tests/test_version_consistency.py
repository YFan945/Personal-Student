from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from test_helpers import load_module

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_installed_version.py"


class VersionConsistencyTests(unittest.TestCase):
    def test_parses_plugin_list_and_details(self) -> None:
        module = load_module(SCRIPT)
        listing = """
> student-presentation-suite@claude-personal
  Version: 0.4.0
  Scope: user
"""
        details = "student-presentation-suite 0.4.0\n  Description"
        self.assertEqual("0.4.0", module.parse_list_version(listing))
        self.assertEqual("0.4.0", module.parse_details_version(details))

    def test_source_versions_are_synchronized(self) -> None:
        module = load_module(SCRIPT)
        versions = module.source_versions()
        self.assertEqual(1, len(set(versions.values())), versions)

    def test_command_output_resolves_windows_cmd_shim(self) -> None:
        module = load_module(SCRIPT)
        completed = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(module.shutil, "which", return_value="C:/bin/claude.cmd"):
            with mock.patch.object(module.subprocess, "run", return_value=completed) as run:
                self.assertEqual("ok", module.command_output("claude", "plugin", "list"))
        self.assertIn("cmd", run.call_args.args[0][0].lower())
        self.assertEqual("C:/bin/claude.cmd", run.call_args.args[0][4])

    def test_extensionless_windows_shim_prefers_cmd(self) -> None:
        module = load_module(SCRIPT)
        completed = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(module.os, "name", "nt"):
            with mock.patch.object(
                module.shutil,
                "which",
                side_effect=lambda name: "C:/bin/claude" if name == "claude" else "C:/bin/claude.cmd",
            ):
                with mock.patch.object(module.subprocess, "run", return_value=completed) as run:
                    module.command_output("claude", "plugin", "list")
        self.assertEqual("C:/bin/claude.cmd", run.call_args.args[0][4])


if __name__ == "__main__":
    unittest.main()
