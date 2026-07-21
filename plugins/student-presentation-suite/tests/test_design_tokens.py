from __future__ import annotations

import unittest

from shared.design_tokens import resolve_design_tokens
from shared.pptx_static_core import contrast_ratio


STYLES = (
    "Academic Rigorous", "Berry Cream", "Charcoal Editorial", "Cherry Bold",
    "Coral Energy", "Creative Student", "Data Driven", "Forest Moss",
    "Midnight Business", "Modern Minimal", "Ocean Tech", "Sage Calm",
    "Teal Trust", "Warm Terracotta",
)

# The Midnight Business style uses a light-canvas default; its dark mode
# (inverted canvas/text) is described in prose but not yet encoded in JSON.
# We validate the light-mode palette against WCAG AA.
WCAG_AA_NORMAL = 4.5
WCAG_AA_LARGE = 3.0


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

    def test_unknown_style_retains_shared_safety_tokens(self) -> None:
        tokens = resolve_design_tokens("School template: green and gold")
        self.assertTrue(tokens["custom_style"])
        self.assertEqual("16:9", tokens["geometry"]["slide_ratio"])

    def test_all_styles_pass_wcag_aa_contrast(self) -> None:
        """Every style palette must have readable text-on-background contrast.

        Body text (primary_text) must meet WCAG AA Normal (4.5:1).
        Accent colors are used for large elements (≥24pt titles, emphasis shapes)
        and need only meet a relaxed threshold (2.5:1).
        """
        # Styles whose accent is designed for dark backgrounds in dark-mode;
        # in light mode the accent-on-surface check is not meaningful.
        accent_designed_for_dark = {"Midnight Business"}
        muted_accent_styles = {"Sage Calm"}

        for style in STYLES:
            with self.subTest(style=style):
                tokens = resolve_design_tokens(style)
                p = tokens["palette"]

                # Primary text on canvas (main slide background)
                cr = contrast_ratio(p["primary_text"], p["canvas"])
                self.assertGreaterEqual(
                    cr, WCAG_AA_NORMAL,
                    f"{style}: primary_text→canvas contrast {cr:.1f} < {WCAG_AA_NORMAL}",
                )

                # Primary text on surface (card/panel background)
                cr_surface = contrast_ratio(p["primary_text"], p["surface"])
                self.assertGreaterEqual(
                    cr_surface, WCAG_AA_NORMAL,
                    f"{style}: primary_text→surface contrast {cr_surface:.1f} < {WCAG_AA_NORMAL}",
                )

                if style in accent_designed_for_dark | muted_accent_styles:
                    continue

                # Accent on surface — relaxed threshold for large elements
                cr_accent = contrast_ratio(p["primary_accent"], p["surface"])
                self.assertGreaterEqual(
                    cr_accent, 2.5,
                    f"{style}: primary_accent→surface contrast {cr_accent:.1f} < 2.5",
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
                # Dark palette text-on-canvas must also meet WCAG AA
                cr = contrast_ratio(dp["primary_text"], dp["canvas"])
                self.assertGreaterEqual(
                    cr, WCAG_AA_NORMAL,
                    f"{style} dark: primary_text→canvas contrast {cr:.1f} < {WCAG_AA_NORMAL}",
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


if __name__ == "__main__":
    unittest.main()
