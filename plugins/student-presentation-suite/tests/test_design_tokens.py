from __future__ import annotations

import unittest

from shared.design_tokens import resolve_design_tokens


class DesignTokenTests(unittest.TestCase):
    def test_all_standard_styles_resolve_to_complete_safety_tokens(self) -> None:
        styles = (
            "Academic Rigorous", "Berry Cream", "Charcoal Editorial", "Cherry Bold",
            "Coral Energy", "Creative Student", "Data Driven", "Forest Moss",
            "Midnight Business", "Modern Minimal", "Ocean Tech", "Sage Calm",
            "Teal Trust", "Warm Terracotta",
        )
        for style in styles:
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


if __name__ == "__main__":
    unittest.main()
