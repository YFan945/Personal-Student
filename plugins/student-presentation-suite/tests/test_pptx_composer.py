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

    def test_svg_library_has_twelve_style_sets(self) -> None:
        body = """
const SVG=require('pptx-svg-library');
const values=Object.keys(SVG.CORNER_SETS).map(name=>SVG.getCornerSvg(name));
console.log(JSON.stringify({count:values.length,valid:values.every(x=>x.startsWith('data:image/svg+xml;base64,'))}));
"""
        result = self.run_node(body)
        self.assertEqual(12, result["count"])
        self.assertTrue(result["valid"])

    def test_optional_style_motif_ignores_custom_unregistered_name(self) -> None:
        body = """
const H=require('pptx-helpers');
const slide={addImage:()=>{throw new Error('must not add an unknown motif')}};
const tokens={svg_reference:{name:'user-drawn-wave'}};
console.log(JSON.stringify({same:H.addStyleMotif(slide,{x:0,y:0,w:10,h:5},tokens)===slide}));
"""
        result = self.run_node(body)
        self.assertTrue(result["same"])

    def test_unlocked_layout_is_advisory_and_does_not_resolve_zones(self) -> None:
        body = """
const C=require('pptx-composer');
const tokens={geometry:{safe_margin_pct:6,footer_zone_pct:5,title_zone_pct:16},palette:{primary_accent:'2563EB'},typography:{title_min_pt:24,body_cjk_min_pt:22,body_latin_min_pt:20,caption_min_pt:10,title_font:'Cambria',body_font:'Calibri'}};
const slide={id:1,title:'A clear claim',kind:'content',layout:'claim-evidence',content:['Evidence','Implication']};
const result=C.resolveSlideComposition(slide,{tokens,history:[],lang:'english'});
console.log(JSON.stringify(result));
"""
        result = self.run_node(body)
        self.assertEqual("adaptive-freeform", result["mode"])
        self.assertFalse(result["exact"])
        self.assertNotIn("zones", result)
        self.assertEqual("claim-evidence", result["layout_hint"])
        self.assertGreaterEqual(len(result["suggestions"]), 2)
        self.assertTrue(all(item["usage"] == "inspiration" for item in result["suggestions"]))

    def test_layout_lock_restores_exact_layout(self) -> None:
        body = """
const C=require('pptx-composer');
const tokens={geometry:{safe_margin_pct:6,footer_zone_pct:5,title_zone_pct:16},palette:{primary_accent:'2563EB'},typography:{title_min_pt:24,body_cjk_min_pt:22,body_latin_min_pt:20,caption_min_pt:10,title_font:'Cambria',body_font:'Calibri'}};
const slide={id:1,title:'Locked cover',kind:'cover',layout:'cover-split',layout_lock:true,content:'Subtitle'};
const result=C.resolveSlideComposition(slide,{tokens,history:[],lang:'english'});
console.log(JSON.stringify(result));
"""
        result = self.run_node(body)
        self.assertEqual("layout-locked", result["mode"])
        self.assertTrue(result["exact"])
        self.assertEqual("cover-split", result["id"])
        self.assertIn("zones", result)

    def test_freeform_preflight_uses_caller_supplied_composition(self) -> None:
        body = """
const C=require('pptx-composer');
const tokens={geometry:{safe_margin_pct:6,footer_zone_pct:5,title_zone_pct:16},palette:{primary_accent:'2563EB'},typography:{title_min_pt:24,body_cjk_min_pt:22,body_latin_min_pt:20,caption_min_pt:10,title_font:'Cambria',body_font:'Calibri'}};
const slide={id:2,title:'Freeform title',kind:'content',layout:'two columns',content:'Short evidence'};
const composition={zones:{title:{x:.6,y:.4,w:8.8,h:.8},body:{x:.6,y:1.5,w:4.2,h:3.2},visual:{x:5.1,y:1.3,w:4.3,h:3.5}},silhouette:'asymmetric-split'};
console.log(JSON.stringify(C.preflightSlide(slide,{tokens,history:[],lang:'english',composition})));
"""
        result = self.run_node(body)
        self.assertTrue(result["ok"])
        self.assertEqual("adaptive-freeform", result["composition_mode"])

    def test_freeform_preflight_blocks_out_of_canvas_zone(self) -> None:
        body = """
const C=require('pptx-composer');
const tokens={geometry:{safe_margin_pct:6,footer_zone_pct:5,title_zone_pct:16},palette:{primary_accent:'2563EB'},typography:{title_min_pt:24,body_cjk_min_pt:22,body_latin_min_pt:20,caption_min_pt:10,title_font:'Cambria',body_font:'Calibri'}};
const slide={id:3,title:'Unsafe composition',kind:'content',layout:'freeform',content:'Evidence'};
const composition={zones:{title:{x:9.5,y:.2,w:1,h:.8},body:{x:.6,y:1.5,w:4.2,h:3.2}},silhouette:'custom'};
console.log(JSON.stringify(C.preflightSlide(slide,{tokens,history:[],lang:'english',composition})));
"""
        result = self.run_node(body)
        self.assertFalse(result["ok"])
        self.assertTrue(any("outside the slide canvas" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
