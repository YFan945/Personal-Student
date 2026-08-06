from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scenario_render_matrix.py"


class ScenarioRenderMatrixTests(unittest.TestCase):
    def test_require_render_refuses_to_silently_skip_when_renderer_missing(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("scenario_render_matrix", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with (
            mock.patch.object(module, "find_soffice", return_value=None),
            mock.patch.object(module, "find_pdftoppm", return_value=None),
            mock.patch.object(sys, "argv", [str(SCRIPT), "--require-render"]),
        ):
            with self.assertRaises(SystemExit) as raised:
                module.main()
        self.assertIn("required", str(raised.exception))

    def test_matrix_covers_all_audited_scenarios(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("scenario_render_matrix", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(9, len(module.MATRIX))
        self.assertIn("school-template-edit", module.MATRIX)
        self.assertIn("data-survey", module.MATRIX)
        families = {
            module.recipe_for(name, index)[1]
            for name, (_, _, roles) in module.MATRIX.items()
            for index in range(len(roles))
        }
        self.assertEqual(
            {
                "hero",
                "visual-dominant",
                "process-path",
                "timeline",
                "comparison",
                "dashboard",
                "architecture",
                "matrix",
                "quote",
                "summary",
                "reference",
            },
            families,
        )
        source = SCRIPT.read_text(encoding="utf-8")
        for scenario in (
            "outline-handoff",
            "review-static-only",
            "review-rendered",
            "review-to-deck",
            "missing-render-incomplete",
            "rebuild",
        ):
            self.assertIn(scenario, source)
        self.assertIn("exercise_school_template_edit", source)
        self.assertIn("exercise_rendered_review", source)
        self.assertIn("slide.addNotes", source)
        self.assertEqual("dashboard", module.recipe_for("school-template-edit", 2)[1])


if __name__ == "__main__":
    unittest.main()
