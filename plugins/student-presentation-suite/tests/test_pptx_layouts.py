from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = ROOT / "scripts" / "pptx-layouts.js"
REGISTRY = ROOT / "skills" / "sp-deck" / "references" / "layout-library.json"


class PptxLayoutsTests(unittest.TestCase):
    def run_node(self, body: str) -> object:
        script = f"const L=require({json.dumps(str(LAYOUTS))});{body}"
        result = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)

    def test_registry_contains_36_unique_bounded_layouts(self) -> None:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        layouts = data["layouts"]
        self.assertEqual(36, len(layouts))
        self.assertEqual(36, len({layout["id"] for layout in layouts}))
        for layout in layouts:
            for zone in layout["zones"].values():
                x, y, width, height = zone
                self.assertGreaterEqual(min(zone), 0)
                self.assertLessEqual(x + width, 1.000001)
                self.assertLessEqual(y + height, 1.000001)
            self.assertIn(layout["fallback"], {item["id"] for item in layouts})
            names = list(layout["zones"])
            overlaps = []
            for index, left in enumerate(names):
                lx, ly, lw, lh = layout["zones"][left]
                for right in names[index + 1 :]:
                    rx, ry, rw, rh = layout["zones"][right]
                    horizontal = min(lx + lw, rx + rw) > max(lx, rx)
                    vertical = min(ly + lh, ry + rh) > max(ly, ry)
                    if horizontal and vertical:
                        overlaps.append((left, right))
            if overlaps:
                self.assertTrue(
                    layout.get("overlap_policy"),
                    f"{layout['id']} has undocumented overlap",
                )

    def test_resolve_maps_normalized_zones_to_safe_area(self) -> None:
        result = self.run_node(
            "console.log(JSON.stringify(L.resolveLayout('cover-split',"
            "{x:1,y:2,w:10,h:5})))"
        )
        self.assertEqual(1, result["zones"]["title"]["x"])
        self.assertEqual(2.6, result["zones"]["title"]["y"])
        self.assertAlmostEqual(4.7, result["zones"]["title"]["w"])

    def test_selector_is_deterministic_and_filters_missing_assets(self) -> None:
        body = """
const context={slideKind:'cover',hasAsset:false,itemCount:1,seed:'stable'};
const tokens={style_dna:{composition:{preferred_layout_tags:['editorial']}}};
const a=L.selectLayouts(context,tokens,[],3);
const b=L.selectLayouts(context,tokens,[],3);
console.log(JSON.stringify({a:a.map(x=>x.id),b:b.map(x=>x.id)}));
"""
        result = self.run_node(body)
        self.assertEqual(result["a"], result["b"])
        self.assertNotIn("cover-full-bleed", result["a"])

    def test_selector_penalizes_third_identical_silhouette(self) -> None:
        body = """
const result=L.selectLayouts(
  {slideKind:'content',itemCount:3,seed:'third'},
  {},
  ['text-two-column','compare-balanced'],
  5
);
console.log(JSON.stringify(result.map(x=>({id:x.id,s:x.silhouette,score:x.score}))));
"""
        result = self.run_node(body)
        self.assertTrue(result)
        self.assertNotEqual("two-column", result[0]["s"])


if __name__ == "__main__":
    unittest.main()
