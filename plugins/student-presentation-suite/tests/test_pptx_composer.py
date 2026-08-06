from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class PptxComposerTests(unittest.TestCase):
    def run_node(self, body: str) -> object:
        env = os.environ.copy()
        env["NODE_PATH"] = os.pathsep.join((str(SCRIPTS), str(ROOT / "node_modules")))
        script = "require('module').Module._initPaths();" + body
        result = subprocess.run(
            ["node", "-e", script], env=env, capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)

    def test_short_component_text_is_centered_both_ways(self) -> None:
        body = """
const H=require('pptx-helpers');
const calls=[]; const slide={addText:(text,options)=>{calls.push({text,options});return options;}};
const tokens={palette:{primary_text:'111827'},typography:{title_min_pt:24,body_cjk_min_pt:22,body_latin_min_pt:20,caption_min_pt:10,title_font:'Cambria',body_font:'Calibri'}};
H.addFittedText(slide,'核心指标',{x:0,y:0,w:2.5,h:1},tokens,'chinese','kpi',{margin:8});
H.addFittedText(slide,'正文保持左对齐',{x:0,y:0,w:4,h:1.5},tokens,'chinese','body',{margin:8});
console.log(JSON.stringify(calls));
"""
        result = self.run_node(body)
        self.assertEqual("center", result[0]["options"]["align"])
        self.assertEqual("mid", result[0]["options"]["valign"])
        self.assertEqual("left", result[1]["options"]["align"])

    def test_text_preflight_blocks_unfit_copy(self) -> None:
        body = """
const H=require('pptx-helpers');
const tokens={palette:{primary_text:'111827'},typography:{title_min_pt:24,body_cjk_min_pt:22,body_latin_min_pt:20,caption_min_pt:10,title_font:'Cambria',body_font:'Calibri'}};
console.log(JSON.stringify(H.preflightText('很长的中文正文'.repeat(80),{x:0,y:0,w:1,h:0.4},tokens,'chinese','body')));
"""
        result = self.run_node(body)
        self.assertFalse(result["ok"])
        self.assertEqual("expand-change-layout-compress-or-split", result["resolution"])

    def test_svg_library_has_fourteen_style_sets(self) -> None:
        body = """
const SVG=require('pptx-svg-library');
const values=Object.keys(SVG.CORNER_SETS).map(name=>SVG.getCornerSvg(name));
console.log(JSON.stringify({count:values.length,valid:values.every(x=>x.startsWith('data:image/svg+xml;base64,'))}));
"""
        result = self.run_node(body)
        self.assertEqual(14, result["count"])
        self.assertTrue(result["valid"])


if __name__ == "__main__":
    unittest.main()
