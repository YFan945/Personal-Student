from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PptxHelperPaletteModeTests(unittest.TestCase):
    def test_dark_mode_switches_every_palette_role_without_mutating_source(self) -> None:
        helper = ROOT / "scripts" / "pptx-helpers.js"
        script = f"""
const H = require({json.dumps(str(helper))});
const source = {{
  palette: {{ canvas: 'FFFFFF', surface: 'F8FAFC', primary_text: '111111', secondary_text: '555555', primary_accent: '0055AA', secondary_accent: '88AACC' }},
  dark_palette: {{ canvas: '111827', surface: '1F2937', primary_text: 'FFFFFF', secondary_text: 'CBD5E1', primary_accent: '93C5FD', secondary_accent: '3B82F6' }}
}};
const dark = H.paletteMode(source, 'dark');
if (dark.palette.canvas !== '111827' || dark.palette.primary_text !== 'FFFFFF') process.exit(2);
if (dark.palette_mode !== 'dark' || source.palette.canvas !== 'FFFFFF') process.exit(3);
const light = H.paletteMode(source, 'light');
if (light.palette.canvas !== 'FFFFFF' || light.palette_mode !== 'light') process.exit(4);
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_dark_mode_rejects_missing_dark_palette(self) -> None:
        helper = ROOT / "scripts" / "pptx-helpers.js"
        script = f"""
const H = require({json.dumps(str(helper))});
try {{ H.paletteMode({{ palette: {{ canvas: 'FFFFFF' }} }}, 'dark'); }}
catch (error) {{ if (error instanceof RangeError) process.exit(0); }}
process.exit(2);
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
