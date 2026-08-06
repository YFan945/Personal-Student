from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_helpers import load_module

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_support_outputs.py"


class SupportOutputTests(unittest.TestCase):
    def test_builds_teleprompter_cards_and_references(self) -> None:
        module = load_module(SCRIPT)
        data = {
            "meta": {"topic": "Demo", "citation_style": "APA"},
            "evidence_ledger": [
                {
                    "id": "e1",
                    "title": "Source",
                    "locator": "https://example.test",
                    "confidence": "high",
                }
            ],
            "slides": [
                {
                    "id": 1,
                    "title": "Claim",
                    "claim": "Main point",
                    "supporting_points": ["Reason"],
                    "speaker_notes": "Explain it.",
                    "transition": "Continue.",
                    "timing_sec": 30,
                }
            ],
        }
        teleprompter = module.teleprompter_html(data)
        cards = module.training_cards(data)
        references = module.references_markdown(data)
        self.assertIn("Explain it.", teleprompter)
        self.assertIn("Likely question", cards)
        self.assertIn("https://example.test", references)

    def test_cli_generates_only_confirmed_or_explicit_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / "spec.json"
            spec.write_text(
                json.dumps(
                    {
                        "meta": {
                            "topic": "Demo",
                            "output_prefix": "demo",
                            "deliverables": ["speaker-notes", "references"],
                        },
                        "slides": [
                            {
                                "id": 1,
                                "title": "Claim",
                                "layout": "claim-focus",
                                "content": "Evidence",
                                "timing_sec": 30,
                                "owner": "A",
                                "speaker_notes": "Explain the evidence.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "outputs"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(spec), "--output-dir", str(output), "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual({"speaker-notes", "references"}, set(payload["outputs"]))
            self.assertFalse((output / "demo-teleprompter.html").exists())

            only = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(spec),
                    "--output-dir",
                    str(output),
                    "--only",
                    "teleprompter",
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, only.returncode, only.stdout + only.stderr)
            self.assertEqual({"teleprompter"}, set(json.loads(only.stdout)["outputs"]))


if __name__ == "__main__":
    unittest.main()
