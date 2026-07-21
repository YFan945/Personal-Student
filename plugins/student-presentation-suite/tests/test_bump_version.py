from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bump_version.py"


def load_module():
    spec = importlib.util.spec_from_file_location("bump_version", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BumpVersionTests(unittest.TestCase):
    def test_set_key_updates_dict(self) -> None:
        module = load_module()
        data = {"version": "0.4.0", "name": "test"}
        result = module._set_key(data, "version", "0.5.0")
        self.assertEqual("0.5.0", result["version"])
        self.assertEqual("test", result["name"])

    def test_current_version_reads_plugin_json(self) -> None:
        module = load_module()
        version = module.current_version()
        self.assertIsInstance(version, str)
        self.assertNotEqual("0.0.0", version)

    def test_bump_dry_run_does_not_write_files(self) -> None:
        module = load_module()
        hashes = {path: path.read_bytes() for path, _, _ in module.FILES_TO_UPDATE}
        result = module.bump("99.99.99", dry_run=True)
        self.assertEqual(0, result)
        for path in hashes:
            self.assertEqual(hashes[path], path.read_bytes(), f"{path} should not be modified during dry-run")

    def test_bump_rejects_invalid_semver(self) -> None:
        module = load_module()
        result = module.bump("banana", dry_run=True)
        self.assertEqual(1, result)

    def test_bump_invalid_file_returns_error(self) -> None:
        module = load_module()
        with mock.patch.object(module, "FILES_TO_UPDATE", [
            (Path("/nonexistent/file.json"), "version",
             lambda data, ver: module._set_key(data, "version", ver)),
        ]):
            result = module.bump("99.99.99", dry_run=True)
            self.assertEqual(1, result)

    def test_update_plugin_entry_raises_on_missing_plugins(self) -> None:
        module = load_module()
        with self.assertRaises(ValueError):
            module._update_plugin_entry({}, "1.0.0")

    def test_update_plugin_entry_raises_on_wrong_plugin(self) -> None:
        module = load_module()
        with self.assertRaises(ValueError):
            module._update_plugin_entry(
                {"plugins": [{"name": "other-plugin", "version": "0.1.0"}]},
                "1.0.0",
            )

    def test_update_plugin_entry_updates_correct_plugin(self) -> None:
        module = load_module()
        result = module._update_plugin_entry(
            {"plugins": [{"name": "student-presentation-suite", "version": "0.4.0"}]},
            "0.5.0",
        )
        self.assertEqual("0.5.0", result["plugins"][0]["version"])


if __name__ == "__main__":
    unittest.main()
