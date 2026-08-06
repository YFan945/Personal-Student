from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from shared.design_tokens import resolve_design_tokens
from shared.pptx_static_core import contrast_ratio

STYLES = (
    "Academic Rigorous", "Berry Cream", "Charcoal Editorial", "Cherry Bold",
    "Coral Energy", "Creative Student", "Data Driven", "Forest Moss",
    "Midnight Business", "Modern Minimal", "Ocean Tech", "Sage Calm",
    "Teal Trust", "Warm Terracotta",
)

WCAG_AA_NORMAL = 4.5
WCAG_AA_LARGE = 3.0
ROOT = Path(__file__).resolve().parents[1]


class DesignTokenTests(unittest.TestCase):
    def test_all_standard_styles_resolve_to_complete_safety_tokens(self) -> None:
        for style in STYLES:
            with self.subTest(style=style):
                tokens = resolve_design_tokens(style)
                self.assertIn("palette", tokens)
                self.assertIn("geometry", tokens)
                self.assertIn("lines", tokens)
                self.assertIn("typography", tokens)
                self.assertEqual("16:9", tokens["geometry"]["slide_ratio"])
                self.assertGreater(tokens["lines"]["standard_pt"], 0)

    def test_style_dna_is_executable_and_structurally_distinct(self) -> None:
        registry = json.loads(
            (ROOT / "skills" / "sp-deck" / "references" / "layout-library.json").read_text(
                encoding="utf-8"
            )
        )
        layout_ids = {layout["id"] for layout in registry["layouts"]}
        dimensions = (
            "shape_grammar",
            "corner_svg_set",
            "component_variants",
            "image_frame",
            "background_treatment",
            "text_alignment_policy",
            "visual_rhythm",
            "fallback_illustration",
        )
        descriptive_dimensions = (
            "composition_bias",
            "shape_line_language",
            "typography_treatment",
            "image_treatment",
            "chart_grammar",
            "signature_motif",
        )
        style_dna = {}
        for style in STYLES:
            with self.subTest(style=style):
                dna = resolve_design_tokens(style)["style_dna"]
                style_dna[style] = dna
                for dimension in dimensions + descriptive_dimensions:
                    self.assertTrue(dna[dimension])
                composition = dna["composition"]
                self.assertGreaterEqual(len(composition["signature_layouts"]), 2)
                self.assertTrue(set(composition["signature_layouts"]).issubset(layout_ids))
                self.assertIn(composition["fallback_layout"], layout_ids)
                self.assertEqual(
                    {"restrained", "standard", "expressive"},
                    set(dna["rhythm_intensity"]),
                )

        for index, left in enumerate(STYLES):
            for right in STYLES[index + 1 :]:
                different = sum(
                    style_dna[left][dimension] != style_dna[right][dimension]
                    for dimension in dimensions
                )
                self.assertGreaterEqual(different, 5, f"{left} and {right} are too similar")

    def test_unknown_style_retains_shared_safety_tokens(self) -> None:
        tokens = resolve_design_tokens("School template: green and gold")
        self.assertTrue(tokens["custom_style"])
        self.assertEqual("16:9", tokens["geometry"]["slide_ratio"])

    def test_all_styles_pass_role_aware_contrast(self) -> None:
        """Text roles meet AA; primary accents remain readable at large sizes."""
        for style in STYLES:
            with self.subTest(style=style):
                tokens = resolve_design_tokens(style)
                p = tokens["palette"]
                for role in ("primary_text", "secondary_text"):
                    for background in ("canvas", "surface"):
                        ratio = contrast_ratio(p[role], p[background])
                        self.assertGreaterEqual(
                            ratio,
                            WCAG_AA_NORMAL,
                            f"{style}: {role}→{background} contrast {ratio:.1f} < {WCAG_AA_NORMAL}",
                        )
                for background in ("canvas", "surface"):
                    ratio = contrast_ratio(p["primary_accent"], p[background])
                    self.assertGreaterEqual(
                        ratio,
                        WCAG_AA_LARGE,
                        f"{style}: primary_accent→{background} contrast {ratio:.1f} < {WCAG_AA_LARGE}",
                    )


    def test_dark_mode_styles_have_dark_palette(self) -> None:
        """Midnight Business and Ocean Tech must provide dark_palette."""
        for style in ("Midnight Business", "Ocean Tech"):
            with self.subTest(style=style):
                tokens = resolve_design_tokens(style)
                self.assertIn("dark_palette", tokens,
                              f"{style} should have dark_palette for dark-mode covers/sections")
                dp = tokens["dark_palette"]
                self.assertIn("canvas", dp)
                self.assertIn("primary_text", dp)
                for role in ("primary_text", "secondary_text"):
                    for background in ("canvas", "surface"):
                        ratio = contrast_ratio(dp[role], dp[background])
                        self.assertGreaterEqual(
                            ratio,
                            WCAG_AA_NORMAL,
                            f"{style} dark: {role}→{background} contrast {ratio:.1f} < {WCAG_AA_NORMAL}",
                        )
                for background in ("canvas", "surface"):
                    ratio = contrast_ratio(dp["primary_accent"], dp[background])
                    self.assertGreaterEqual(
                        ratio,
                        WCAG_AA_LARGE,
                        f"{style} dark: primary_accent→{background} contrast {ratio:.1f} < {WCAG_AA_LARGE}",
                    )

    def test_non_dark_styles_do_not_have_dark_palette(self) -> None:
        """Styles without dark mode should not have dark_palette."""
        dark_styles = {"Midnight Business", "Ocean Tech"}
        for style in STYLES:
            if style in dark_styles:
                continue
            with self.subTest(style=style):
                tokens = resolve_design_tokens(style)
                self.assertNotIn("dark_palette", tokens,
                                 f"{style} should not have dark_palette")

    def test_style_files_keep_field_order_and_match_palette_tokens(self) -> None:
        fields = [
            "Palette", "Visual character", "Use when", "Creative freedom",
            "Guardrails", "Typography", "Slide rhythm", "Charts and diagrams",
            "Layout motif", "Fallback layout", "Color roles", "Geometry",
            "Slide recipes", "Image treatment", "Density control",
            "Acceptance checks", "Do not sacrifice", "Avoid",
        ]
        style_dir = ROOT / "skills" / "sp-deck" / "references" / "visual-styles"
        for style in STYLES:
            with self.subTest(style=style):
                tokens = resolve_design_tokens(style)
                path = style_dir / f"{tokens['style_key']}.md"
                text = path.read_text(encoding="utf-8")
                actual = re.findall(r"^- \*\*([^:]+):\*\*", text, flags=re.MULTILINE)
                self.assertEqual(fields, actual)
                self.assertNotIn("## 通用设计原则", text)
                for palette_name in ("palette", "dark_palette"):
                    for value in tokens.get(palette_name, {}).values():
                        self.assertIn(str(value), text, f"{path.name} misses token {value}")
                allowed_colors = {
                    str(value).upper()
                    for palette_name in ("palette", "dark_palette")
                    for value in tokens.get(palette_name, {}).values()
                }
                referenced_colors = set(re.findall(r"`([0-9A-Fa-f]{6})`", text))
                self.assertTrue(
                    referenced_colors.issubset(allowed_colors),
                    f"{path.name} references unmodeled colors {sorted(referenced_colors - allowed_colors)}",
                )

    def test_style_files_do_not_force_one_component_on_every_slide(self) -> None:
        style_dir = ROOT / "skills" / "sp-deck" / "references" / "visual-styles"
        forbidden = ("每页必须", "每页一个系统/流程图", "每页一个用户旅程", "5-7 nodes")
        visual_source = (ROOT / "scripts" / "pptx-visuals.js").read_text(encoding="utf-8")
        component_names = set(re.findall(r"function (add[A-Za-z]+)\(", visual_source))
        for path in style_dir.glob("*.md"):
            with self.subTest(style=path.name):
                text = path.read_text(encoding="utf-8")
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)
                for component in re.findall(r"`(add[A-Za-z]+)`", text):
                    self.assertIn(component, component_names, f"unknown component {component}")


if __name__ == "__main__":
    unittest.main()
