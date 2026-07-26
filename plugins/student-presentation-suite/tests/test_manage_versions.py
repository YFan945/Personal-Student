from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_helpers import load_module

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "manage_versions.py"


class ManageVersionsTests(unittest.TestCase):
    def test_snapshot_and_restore_candidate(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "outputs"
            output.mkdir()
            deck = output / "demo.pptx"
            deck.write_bytes(b"demo")
            saved = module.snapshot(output, "r1", [deck])
            deck.write_bytes(b"changed")
            restored = module.restore_candidate(output, "r1")
            candidate = Path(restored["restored_root"]) / "demo.pptx"
            self.assertEqual(b"demo", candidate.read_bytes())
            self.assertEqual(b"changed", deck.read_bytes())
            self.assertTrue(Path(saved["revision_root"]).is_dir())


if __name__ == "__main__":
    unittest.main()
