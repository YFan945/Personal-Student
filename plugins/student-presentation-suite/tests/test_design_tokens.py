from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from shared.design_tokens import resolve_design_tokens, validate_custom_style
from shared.pptx_static_core import contrast_ratio

STYLES = (
    "Academic Rigorous",
    "Data Driven",
    "Modern Minimal",
    "Charcoal Editorial",
    "Midnight Business",
    "Ocean Tech",
    "Teal Trust",
    "Cherry Bold",
    "Creative Student",
    "Coral Energy",
    "Forest Moss",
    "Warm Terracotta",
)
ROOT = Path(__file__).resolve().parents[1]


class DesignTokenTests(unittest.TestCase):
    def test_catalog_has_three_categories_of_four_unique_styles(self) -> None:
        catalog = json.loads((ROOT / "references" / "design-tokens.json").read_text(encoding="utf-8"))
        self.assertEqual(12, len(catalog["styles"]))
        self.assertEqual(3, len(catalog["categories"]))
        flattened = [key for values in catalog["categories"].values() for key in values]
        self.assertEqual(12, len(flattened))
        self.assertEqual(12, len(set(flattened)))
        self.assertEqual(set(catalog["styles"]), set(flattened))
        self.assertTrue(all(len(values) == 4 for values in catalog["categories"].values()))

    def test_all_standard_styles_resolve_to_lightweight_safety_tokens(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                tokens = resolve_design_tokens(style)
                for field in ("style_character", "palette", "backgrounds", "svg_reference"):
                    self.assertIn(field, tokens)
                for shared in ("geometry", "lines", "typography"):
                    self.assertIn(shared, tokens)
                self.assertNotIn("style_dna", tokens)
                self.assertEqual("16:9", tokens["geometry"]["slide_ratio"])

    def test_legacy_aliases_map_with_compatibility_warning(self) -> None:
        cases = {
            "Berry Cream": "Warm Terracotta",
            "berry-cream": "Warm Terracotta",
            "Sage Calm": "Forest Moss",
            "sage-calm": "Forest Moss",
        }
        for old, expected in cases.items():
            with self.subTest(old=old):
                tokens = resolve_design_tokens(old)
                self.assertEqual(expected, tokens["style_name"])
                self.assertTrue(tokens["compatibility_warnings"])

    def test_other_requires_and_resolves_complete_custom_reference(self) -> None:
        custom = {
            "style_character": "Quiet scientific field notes",
            "palette": {
                "canvas": "FFFFFF",
                "surface": "F5F5F5",
                "primary_text": "111111",
                "secondary_text": "555555",
                "primary_accent": "2563EB",
                "secondary_accent": "93C5FD",
            },
            "backgrounds": {
                "cover": "Blue field",
                "content": "White canvas",
                "section": "Pale blue field",
                "closing": "Blue field",
            },
            "svg_reference": {"name": "none", "usage": "No recurring SVG motif"},
        }
        self.assertEqual([], validate_custom_style(custom))
        tokens = resolve_design_tokens("Other", custom)
        self.assertEqual("Other", tokens["style_name"])
        self.assertEqual(custom["palette"], tokens["palette"])
        with self.assertRaises(ValueError):
            resolve_design_tokens("Other")
        low_contrast = json.loads(json.dumps(custom))
        low_contrast["palette"]["secondary_text"] = "EEEEEE"
        self.assertTrue(any("4.5:1" in item for item in validate_custom_style(low_contrast)))
        with_extra = json.loads(json.dumps(custom))
        with_extra["layout_preference"] = "two-column"
        self.assertTrue(any("unsupported fields" in item for item in validate_custom_style(with_extra)))

    def test_unknown_style_uses_safe_reference_and_warning(self) -> None:
        tokens = resolve_design_tokens("School template: green and gold")
        self.assertTrue(tokens["custom_style"])
        self.assertEqual("School template: green and gold", tokens["style_character"])
        self.assertTrue(tokens["compatibility_warnings"])
        self.assertEqual("16:9", tokens["geometry"]["slide_ratio"])

    def test_all_styles_pass_role_aware_contrast(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                palette = resolve_design_tokens(style)["palette"]
                for role in ("primary_text", "secondary_text"):
                    for background in ("canvas", "surface"):
                        self.assertGreaterEqual(contrast_ratio(palette[role], palette[background]), 4.5)
                for background in ("canvas", "surface"):
                    self.assertGreaterEqual(contrast_ratio(palette["primary_accent"], palette[background]), 3.0)

    def test_style_files_have_exact_four_fields_and_match_tokens(self) -> None:
        expected_fields = ["Style character", "Palette", "Background reference", "SVG reference"]
        style_dir = ROOT / "skills" / "sp-deck" / "references" / "visual-styles"
        self.assertEqual(12, len(list(style_dir.glob("*.md"))))
        for style in STYLES:
            with self.subTest(style=style):
                tokens = resolve_design_tokens(style)
                text = (style_dir / f"{tokens['style_key']}.md").read_text(encoding="utf-8")
                actual = re.findall(r"^- \*\*([^:]+):\*\*", text, flags=re.MULTILINE)
                self.assertEqual(expected_fields, actual)
                for value in tokens["palette"].values():
                    self.assertIn(str(value), text)
                self.assertIn(tokens["svg_reference"]["name"], text)


if __name__ == "__main__":
    unittest.main()
