from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from test_helpers import load_module


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "create_revision_manifest.py"


class RevisionManifestTests(unittest.TestCase):
    def write(self, path: Path, title: str, locked: bool) -> None:
        path.write_text(
            yaml.safe_dump(
                {
                    "revision": {"revision_id": path.stem},
                    "slides": [
                        {
                            "id": 1,
                            "title": title,
                            "layout": "content",
                            "content": "Point",
                            "timing_sec": 30,
                            "owner": "Individual",
                            "locked": locked,
                            "lock_reason": "approved" if locked else None,
                        }
                    ],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

    def test_locked_slide_change_is_violation(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "r1.yaml"
            new = Path(tmp) / "r2.yaml"
            self.write(old, "Approved", True)
            self.write(new, "Changed", True)
            manifest = module.build_manifest(old, new, "rewrite")
        self.assertFalse(manifest["valid"])
        self.assertEqual([1], manifest["changed_slides"])

    def test_unlocked_slide_change_is_valid(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "r1.yaml"
            new = Path(tmp) / "r2.yaml"
            self.write(old, "Before", False)
            self.write(new, "After", False)
            manifest = module.build_manifest(old, new, "rewrite")
        self.assertTrue(manifest["valid"])

    def test_change_outside_target_scope_is_violation(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "r1.yaml"
            new = Path(tmp) / "r2.yaml"
            self.write(old, "Before", False)
            self.write(new, "After", False)
            payload = yaml.safe_load(new.read_text(encoding="utf-8"))
            payload["revision_operation"] = "rewrite-slide"
            payload["target_slides"] = [2]
            new.write_text(yaml.safe_dump(payload), encoding="utf-8")
            manifest = module.build_manifest(old, new, "rewrite")
        self.assertFalse(manifest["valid"])
        self.assertIn("outside", manifest["violations"][0]["problem"])


if __name__ == "__main__":
    unittest.main()
