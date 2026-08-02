#!/usr/bin/env python3
"""Generate, render, and strictly validate representative student PPTX scenarios.

Generated artifacts remain in a temporary directory.  CI should invoke this with
``--require-render`` on a runner that has LibreOffice and Poppler installed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.pptx_runtime.render import find_pdftoppm, find_soffice
from shared.slide_spec_validation import semantic_errors

MATRIX = {
    "coursework-zh": ("coursework", "Chinese", ["background", "method", "evidence", "conclusion"]),
    "english-class": ("coursework", "English", ["background", "method", "evidence", "conclusion"]),
    "defense-zh": ("defense", "Chinese", ["problem", "method", "result", "value", "limitation", "qa"]),
    "competition-zh": ("competition", "Chinese", ["problem", "solution", "method", "result", "value", "limitation"]),
    "club-bilingual": ("club-showcase", "bilingual", ["opening", "method", "result", "value"]),
    "research-zh": ("research", "Chinese", ["problem", "background", "method", "result", "limitation", "conclusion"]),
    "software-project": ("coursework", "Chinese", ["problem", "method", "evidence", "conclusion"]),
    "data-survey": ("research", "Chinese", ["problem", "background", "method", "result", "limitation", "conclusion"]),
    "school-template-edit": ("coursework", "Chinese", ["background", "method", "evidence", "conclusion"]),
}

VISUAL_RECIPES = (
    (
        "comparison",
        "comparison",
        {"items": ["Current", "Target"], "dimensions": ["clarity", "evidence"]},
    ),
    (
        "process",
        "process-path",
        {"steps": ["Frame", "Build", "Verify"]},
    ),
    (
        "chart",
        "dashboard",
        {
            "measure": "quality score",
            "unit": "points",
            "scope": "scenario matrix",
            "source": "generated fixture",
            "takeaway": "the runtime completes the scenario",
            "title": "Scenario quality",
            "series": [
                {
                    "name": "Score",
                    "labels": ["Plan", "Produce", "QA"],
                    "values": [72, 88, 96],
                }
            ],
            "metrics": [
                {"value": "3", "label": "stages"},
                {"value": "1", "label": "candidate"},
                {"value": "0", "label": "blockers"},
            ],
        },
    ),
    (
        "matrix",
        "matrix",
        {
            "items": [
                {"label": "Content", "x": 0.25, "y": 0.7},
                {"label": "Visual", "x": 0.55, "y": 0.85},
                {"label": "QA", "x": 0.8, "y": 0.6},
            ]
        },
    ),
    (
        "architecture",
        "architecture",
        {"nodes": ["Spec", "Generator", "PPTX", "QA"]},
    ),
    (
        "timeline",
        "timeline",
        {"stages": ["Plan", "Produce", "Render", "Deliver"]},
    ),
    (
        "hero",
        "hero",
        {"title": "Scenario checkpoint", "subtitle": "One claim, one visual focus"},
    ),
    (
        "diagram",
        "visual-dominant",
        {"annotations": ["Subject", "Evidence", "Takeaway"]},
    ),
    (
        "quote",
        "quote",
        {"quote": "Clear visuals verify.", "source": "Fixture"},
    ),
    (
        "summary",
        "summary",
        {"takeaways": ["Plan", "Generate", "Verify"]},
    ),
    (
        "reference",
        "reference",
        {"references": ["Scenario fixture (2026)", "Suite runtime documentation"]},
    ),
)


def recipe_for(name: str, index: int) -> tuple[str, str, dict[str, object]]:
    offset = sum(name.encode("utf-8")) % len(VISUAL_RECIPES)
    return VISUAL_RECIPES[(offset + index) % len(VISUAL_RECIPES)]


def run_checked(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise RuntimeError(f"{label} failed\n{result.stdout}\n{result.stderr}")
    return result


def generate_deck(work: Path, name: str, language: str, roles: list[str]) -> Path:
    deck = work / f"{name}.js"
    pptx = work / f"{name}-presentation.pptx"
    role_json = json.dumps(roles, ensure_ascii=False)
    recipes_json = json.dumps(
        [
            {
                "family": recipe_for(name, index)[1],
                **recipe_for(name, index)[2],
            }
            for index in range(len(roles))
        ],
        ensure_ascii=False,
    )
    deck.write_text(f"""
const pptxgen = require('pptxgenjs');
const H = require('pptx-helpers');
const V = require('pptx-visuals');
const TOKENS = {{
  palette: {{ canvas: 'F8FAFC', primary_text: '111827', secondary_text: '4B5563' }},
  typography: {{ title_min_pt: 24, body_cjk_min_pt: 22, body_latin_min_pt: 20,
                 title_font: 'Cambria', body_font: 'Calibri' }},
  geometry: {{ safe_margin_pct: 6, title_zone_pct: 16, footer_zone_pct: 5,
               spacing_scale_pt: [6, 12, 18, 24, 36, 48], corner_radius_pt: 8 }}
}};
const pptx = new pptxgen();
H.applyTokens(pptx, TOKENS, '{language.lower()}');
const roles = {role_json};
const recipes = {recipes_json};
for (const [index, role] of roles.entries()) {{
  const slide = pptx.addSlide(); slide.background = {{ color: 'F8FAFC' }};
  const area = H.safeArea(H.SLIDE_W_IN, H.SLIDE_H_IN, TOKENS);
  H.addTitle(slide, `${{index + 1}}. ${{role}}`, area, TOKENS, '{language.lower()}');
  V.renderVisual(slide, recipes[index].family, recipes[index], area, TOKENS, '{language.lower()}');
}}
pptx.writeFile({{ fileName: process.argv[2] }});
""", encoding="utf-8")
    subprocess.run(
        [
            "node",
            str(ROOT / "scripts" / "run_with_pptxgenjs.js"),
            "--output",
            str(pptx),
            str(deck),
        ],
        check=True,
    )
    return pptx


def validate_scenario(
    work: Path,
    name: str,
    scenario: str,
    language: str,
    roles: list[str],
) -> tuple[Path, Path, Path]:
    data = {
        "schema_version": "2.0",
        "meta": {
            "scenario": scenario,
            "language": language,
            "slide_count": len(roles),
            "visual_text_ratio": "balanced",
        },
        "slides": [
            {
                "id": index + 1,
                "title": role,
                "layout": recipe_for(name, index)[1],
                "content": role,
                "role": role,
                "timing_sec": 30,
                "owner": "A",
                "visual": {
                    "type": recipe_for(name, index)[0],
                    "purpose": f"Exercise the {role} visual structure",
                    "layout_family": recipe_for(name, index)[1],
                    "details": recipe_for(name, index)[2],
                },
            }
            for index, role in enumerate(roles)
        ],
    }
    errors = semantic_errors(data)
    if errors:
        raise RuntimeError(f"Scenario contract failed for {name}: {errors}")
    spec_path = work / f"{name}-slide-spec.json"
    spec_report = work / f"{name}-slide-spec-report.json"
    visual_plan = work / f"{name}-visual-plan.json"
    spec_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_slide_spec.py"),
            str(spec_path),
            "--output",
            str(spec_report),
            "--json",
        ],
        f"{name}: Slide Spec validation",
    )
    run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "compile_visual_plan.py"),
            str(spec_path),
            "--output",
            str(visual_plan),
            "--json",
        ],
        f"{name}: visual plan",
    )
    return spec_path, spec_report, visual_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Run temporary rendered PPTX scenario matrix")
    parser.add_argument("--require-render", action="store_true")
    args = parser.parse_args()
    if not find_soffice() or not find_pdftoppm():
        if args.require_render:
            raise SystemExit("LibreOffice soffice and pdftoppm are required for the render matrix.")
        print(json.dumps({"ok": True, "skipped": True, "reason": "LibreOffice or Poppler unavailable"}))
        return
    delivery = ROOT / "skills" / "student-presentation-ppt" / "scripts" / "pptx_delivery_check.py"
    tool = ROOT / "scripts" / "pptx_tool.py"
    completed = []
    with tempfile.TemporaryDirectory(prefix="student-presentation-matrix-") as tmp:
        work = Path(tmp)
        for name, (scenario, language, roles) in MATRIX.items():
            spec_path, spec_report, _visual_plan = validate_scenario(
                work, name, scenario, language, roles
            )
            pptx = generate_deck(work, name, language, roles)
            notes = work / f"{name}-speaker-notes.md"
            notes.write_text("# Matrix notes\n", encoding="utf-8")
            package_report = work / f"{name}-package-report.json"
            run_checked(
                [sys.executable, str(tool), "validate", str(pptx), "--output", str(package_report), "--json"],
                f"{name}: package validation",
            )
            render_dir = work / f"{name}-render"
            render_result = run_checked(
                [sys.executable, str(tool), "render", str(pptx), "--output-dir", str(render_dir), "--prefix", name],
                f"{name}: render",
            )
            render_payload = json.loads(render_result.stdout)
            if os.environ.get("PPTX_RUNTIME_FORCE_AF_UNIX_SHIM") == "1" and not any(
                "AF_UNIX denial simulation active" in message
                for message in render_payload.get("messages", [])
            ):
                raise RuntimeError(f"{name}: forced AF_UNIX shim was not activated")
            pages = sorted(render_dir.glob(f"{name}-*.png"))
            if len(pages) != len(roles):
                raise RuntimeError(f"{name}: rendered {len(pages)} pages for {len(roles)} slides")
            if not package_report.is_file():
                raise RuntimeError(f"{name}: package validation did not publish a report")
            manifest = work / f"{name}-qa-manifest.json"
            manifest_command = [
                sys.executable,
                str(tool),
                "qa-manifest",
                "--pptx",
                str(pptx),
                "--output",
                str(manifest),
                "--no-repair-needed-reason",
                "CI rendered scenario baseline.",
                "--slide-spec-report",
                str(spec_report),
                "--slide-spec",
                str(spec_path),
                "--package-report",
                str(package_report),
            ]
            for page in pages:
                manifest_command.extend(["--preview", str(page)])
            run_checked(manifest_command, f"{name}: QA manifest")
            delivery_command = [
                sys.executable,
                str(delivery),
                "--pptx",
                str(pptx),
                "--notes",
                str(notes),
                "--qa-manifest",
                str(manifest),
                "--package-report",
                str(package_report),
                "--strict",
                "--json",
            ]
            for page in pages:
                delivery_command.extend(["--preview", str(page)])
            run_checked(delivery_command, f"{name}: strict delivery")
            completed.append(name)
    print(json.dumps({"ok": True, "rendered_scenarios": completed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
