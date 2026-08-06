from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.visual_system_smoke_gallery import layout_deck_source, style_deck_source, svg_atlas_source
from shared.design_tokens import resolve_design_tokens

ROOT = Path(__file__).resolve().parents[1]


class VisualSystemSmokeGalleryTests(unittest.TestCase):
    def test_style_gallery_covers_all_styles_with_eight_slide_jobs(self) -> None:
        catalog = json.loads((ROOT / "references" / "design-tokens.json").read_text(encoding="utf-8"))
        self.assertEqual(14, len(catalog["styles"]))
        for style_key in catalog["styles"]:
            with self.subTest(style=style_key):
                source = style_deck_source(resolve_design_tokens(style_key))
                self.assertEqual(8, source.count("= baseSlide("))
                for family in ("quote", "dashboard", "process-path", "summary"):
                    self.assertIn(f"'{family}'", source)
                self.assertIn("L.selectLayouts", source)
                self.assertIn("H.addStyleMotif", source)
                self.assertIn("hasAsset:false", source)
                self.assertIn("missing-asset fallback", source)
                self.assertIn("SVG.addCornerDecoration", source)

    def test_layout_gallery_contains_all_36_layout_ids(self) -> None:
        registry = json.loads((ROOT / "skills" / "sp-deck" / "references" / "layout-library.json").read_text(encoding="utf-8"))
        source = layout_deck_source(resolve_design_tokens("Modern Minimal"), registry)
        self.assertEqual(36, len(registry["layouts"]))
        self.assertIn("L.resolveLayout", source)
        self.assertIn("renderLayoutSample", source)
        self.assertIn("V.renderVisual", source)
        for layout in registry["layouts"]:
            self.assertIn(layout["id"], source)

    def test_svg_atlas_contains_all_style_corner_sets(self) -> None:
        source = svg_atlas_source(resolve_design_tokens("Modern Minimal"))
        self.assertIn("SVG.CORNER_SETS", source)
        self.assertIn("SVG.addCornerDecoration", source)


if __name__ == "__main__":
    unittest.main()
