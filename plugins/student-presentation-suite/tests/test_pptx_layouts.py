from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = ROOT / "scripts" / "pptx-layouts.js"
REGISTRY = ROOT / "skills" / "sp-deck" / "references" / "layout-library.json"
SCHEMA = ROOT / "skills" / "sp-deck" / "references" / "layout-library.schema.json"


class PptxLayoutsTests(unittest.TestCase):
    def run_node(self, body: str) -> object:
        script = f"const L=require({json.dumps(str(LAYOUTS))});{body}"
        result = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)

    def test_registry_contains_36_unique_bounded_layouts(self) -> None:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual([], list(Draft202012Validator(schema).iter_errors(data)))
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
        self.assertIn("composition", result)
        self.assertIn("shape_slots", result)
        self.assertIn("text_policy", result)
        self.assertIn("asset_slots", result)
        self.assertIn("corner_decoration", result)
        self.assertIn("variant_fallbacks", result)

    def test_all_layouts_resolve_to_supported_composition_shapes(self) -> None:
        body = """
const allowed=new Set(['rect','roundRect','ellipse','pill','hexagon','chevron','parallelogram','arch','bracket','none']);
const resolved=L.registry.layouts.map(x=>L.getLayout(x.id));
console.log(JSON.stringify({count:resolved.length,valid:resolved.every(x=>x.shape_slots.every(s=>allowed.has(s.shape))),shapes:[...new Set(resolved.flatMap(x=>x.shape_slots.map(s=>s.shape)))]}));
"""
        result = self.run_node(body)
        self.assertEqual(36, result["count"])
        self.assertTrue(result["valid"])
        self.assertGreaterEqual(len(set(result["shapes"]) - {"rect", "roundRect", "none"}), 6)

    def test_selector_is_deterministic_and_filters_missing_assets(self) -> None:
        body = """
const context={slideKind:'cover',hasAsset:false,itemCount:1,seed:'stable'};
const tokens={palette:{primary_accent:'2563EB'}};
const a=L.selectLayouts(context,tokens,[],3);
const b=L.selectLayouts(context,tokens,[],3);
console.log(JSON.stringify({a:a.map(x=>x.id),b:b.map(x=>x.id)}));
"""
        result = self.run_node(body)
        self.assertEqual(result["a"], result["b"])
        self.assertNotIn("cover-full-bleed", result["a"])

    def test_selector_returns_adaptable_inspiration_not_exact_coordinates(self) -> None:
        payload = self.run_node(
            """
const result=L.suggestLayouts({slideKind:'content',layout:'claim-evidence',itemCount:2},{},[],3);
console.log(JSON.stringify(result));
"""
        )
        self.assertEqual(3, len(payload))
        for item in payload:
            self.assertEqual("inspiration", item["usage"])
            self.assertTrue(item["adaptable"])
            self.assertNotIn("safeArea", item)
            self.assertNotIn("mirrored", item)

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

    def test_selector_accepts_slide_spec_native_kind_and_visual_enums(self) -> None:
        body = """
const section=L.selectLayouts({slideKind:'section-divider',itemCount:1}, {}, [], 3);
const quotation=L.selectLayouts({slideKind:'quotation',visualFamily:'quote',hasQuote:true,itemCount:1}, {}, [], 3);
const dashboard=L.selectLayouts({slideKind:'content',visualFamily:'dashboard',hasData:true,itemCount:3}, {}, [], 3);
console.log(JSON.stringify({section:section.map(x=>x.family),quotation:quotation.map(x=>x.id),dashboard:dashboard.map(x=>x.family)}));
"""
        result = self.run_node(body)
        self.assertTrue(result["section"])
        self.assertEqual({"section"}, set(result["section"]))
        self.assertTrue(result["quotation"])
        self.assertTrue(all(item.startswith("quote-") for item in result["quotation"]))
        self.assertTrue(result["dashboard"])
        self.assertEqual({"data"}, set(result["dashboard"]))

    def test_selector_enforces_capacity_and_contraindications(self) -> None:
        body = """
const longTitle=L.selectLayouts({slideKind:'cover',title:'x'.repeat(50),itemCount:1}, {}, [], 10);
const blocked=L.selectLayouts({slideKind:'cover',itemCount:1,contraindications:['dense-agenda']}, {}, [], 10);
console.log(JSON.stringify({longTitle:longTitle.map(x=>x.id),blocked:blocked.map(x=>x.id)}));
"""
        result = self.run_node(body)
        self.assertNotIn("cover-split", result["longTitle"])
        self.assertNotIn("cover-full-bleed", result["longTitle"])
        self.assertNotIn("cover-minimal", result["blocked"])
        self.assertNotIn("cover-split", result["blocked"])

    def test_selector_rejects_narrow_title_zone_for_long_cjk_title(self) -> None:
        body = """
const result=L.selectLayouts(
  {slideKind:'content',visualFamily:'visual-dominant',hasAsset:false,itemCount:3,title:'核心观点：长中文标题与素材缺失时仍须保持清晰层级'},
  {palette:{primary_accent:'990011'}},
  [],
  3
);
const payload=result.map(x=>({id:x.id,titleZone:x.zones.title}));
console.log(JSON.stringify(payload));
"""
        result = self.run_node(body)
        self.assertTrue(result)
        self.assertTrue(all(item["titleZone"][2] >= 0.9 for item in result))

    def test_selector_order_is_independent_of_visual_style_tokens(self) -> None:
        body = """
const context={slideKind:'content',visualFamily:'dashboard',hasData:true,itemCount:3,seed:'same'};
const history=['claim-focus'];
const a=L.selectLayouts(context,{palette:{primary_accent:'2563EB'},style_character:'minimal'},history,5);
const b=L.selectLayouts(context,{palette:{primary_accent:'990011'},style_character:'bold'},history,5);
console.log(JSON.stringify({a:a.map(x=>x.id),b:b.map(x=>x.id)}));
"""
        result = self.run_node(body)
        self.assertEqual(result["a"], result["b"])


if __name__ == "__main__":
    unittest.main()
