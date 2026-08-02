from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from shared.visual_plan import compile_visual_plan

ROOT = Path(__file__).resolve().parents[1]


def slide(index: int, role: str, visual_type: str, family: str) -> dict:
    return {
        "id": index,
        "title": role,
        "layout": family,
        "kind": "content",
        "role": role,
        "content": role,
        "timing_sec": 30,
        "owner": "A",
        "visual": {
            "type": visual_type,
            "purpose": f"Explain {role}",
            "layout_family": family,
        },
    }


class VisualPlanTests(unittest.TestCase):
    def test_strict_plan_rejects_text_only_content(self) -> None:
        result = compile_visual_plan(
            {
                "schema_version": "2.0",
                "meta": {"quality_level": "high-score"},
                "slides": [
                    {
                        "id": 1,
                        "title": "Problem",
                        "layout": "content",
                        "content": "Problem",
                        "timing_sec": 30,
                        "owner": "A",
                    }
                ],
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("meaningful editable visual", str(result["errors"]))

    def test_strict_plan_accepts_diverse_editable_layout_families(self) -> None:
        result = compile_visual_plan(
            {
                "schema_version": "2.0",
                "meta": {"quality_level": "high-score"},
                "slides": [
                    slide(1, "problem", "comparison", "comparison"),
                    slide(2, "method", "process", "process-path"),
                    slide(3, "result", "chart", "dashboard"),
                    slide(4, "limitation", "matrix", "matrix"),
                ],
            }
        )
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(1.0, result["metrics"]["meaningful_visual_coverage"])
        self.assertEqual(4, result["metrics"]["layout_family_count"])

    def test_strict_plan_rejects_three_identical_layouts(self) -> None:
        result = compile_visual_plan(
            {
                "schema_version": "2.0",
                "meta": {"quality_level": "high-score"},
                "slides": [
                    slide(index, "result", "chart", "dashboard")
                    for index in range(1, 4)
                ],
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("repeats more than twice", str(result["errors"]))

    def test_cli_binds_output_to_slide_spec_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / "spec.json"
            output = root / "visual-plan.json"
            spec.write_text(
                json.dumps(
                    {
                        "slides": [
                            {
                                "id": 1,
                                "title": "Cover",
                                "layout": "hero",
                                "kind": "cover",
                                "content": "Cover",
                                "timing_sec": 30,
                                "owner": "A",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "compile_visual_plan.py"),
                    str(spec),
                    "--output",
                    str(output),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(payload["slide_spec_sha256"])
        self.assertEqual("addSectionHero", payload["slides"][0]["component"])

    def test_editable_visual_library_exports_and_renders_process(self) -> None:
        if not (ROOT / "node_modules" / "pptxgenjs").is_dir():
            self.skipTest("pptxgenjs runtime is unavailable")
        script = """
const V=require('./scripts/pptx-visuals.js');
const calls=[];
const slide={
  addShape:(...a)=>calls.push(['shape',...a]),
  addText:(...a)=>calls.push(['text',...a]),
};
const tokens={
  palette:{canvas:'FFFFFF',surface:'F4F4F5',primary_text:'111827',
    secondary_text:'4B5563',primary_accent:'2563EB',secondary_accent:'F97316'},
  typography:{title_min_pt:24,body_cjk_min_pt:22,body_latin_min_pt:20,
    title_font:'Aptos Display',body_font:'Aptos'},
  geometry:{spacing_scale_pt:[6,12,18,24,36,48],corner_radius_pt:8},
};
V.renderVisual(slide,'process-path',{steps:['Define','Build','Verify']},
  {x:0.6,y:1.2,w:8.8,h:3.6},tokens,'english');
process.stdout.write(JSON.stringify({exports:Object.keys(V),calls:calls.length}));
"""
        env = os.environ.copy()
        env["NODE_PATH"] = str(ROOT / "scripts")
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("addArchitecture", payload["exports"])
        self.assertGreaterEqual(payload["calls"], 8)

    def test_visual_spec_flattens_details_and_contains_image(self) -> None:
        if not (ROOT / "node_modules" / "pptxgenjs").is_dir():
            self.skipTest("pptxgenjs runtime is unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / "wide.png"
            Image.new("RGB", (400, 200), "navy").save(asset)
            script = f"""
const V=require('./scripts/pptx-visuals.js');
const images=[];
const slide={{
  addShape:()=>{{}},
  addText:()=>{{}},
  addImage:(options)=>images.push(options),
}};
const tokens={{
  palette:{{canvas:'FFFFFF',surface:'F4F4F5',primary_text:'111827',
    secondary_text:'4B5563',primary_accent:'2563EB',secondary_accent:'F97316'}},
  typography:{{title_min_pt:24,body_cjk_min_pt:22,body_latin_min_pt:20,
    title_font:'Aptos Display',body_font:'Aptos'}},
  geometry:{{spacing_scale_pt:[6,12,18,24,36,48],corner_radius_pt:8}},
}};
V.renderVisualSpec(slide,{{
  type:'annotated-image',
  asset:{json.dumps(str(asset))},
  alt_text:'Wide evidence image',
  details:{{annotations:['One','Two']}},
}},'visual-dominant',{{x:0,y:0,w:10,h:4}},tokens,'english');
process.stdout.write(JSON.stringify(images[0]));
"""
            env = os.environ.copy()
            env["NODE_PATH"] = str(ROOT / "scripts")
            result = subprocess.run(
                ["node", "-e", script],
                cwd=ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        image = json.loads(result.stdout)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("Wide evidence image", image["altText"])
        # addAnnotatedVisual reserves 56% of the area for the image box; the
        # 2:1 asset is contained within it.
        self.assertAlmostEqual(5.6, image["w"], places=2)
        self.assertAlmostEqual(2.8, image["h"], places=2)


if __name__ == "__main__":
    unittest.main()
