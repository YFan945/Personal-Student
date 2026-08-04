#!/usr/bin/env python3
"""Generate and validate a minimal PPTX through the runtime wrapper."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="student-presentation-smoke-") as tmp:
        work = Path(tmp)
        pptx = work / "smoke-presentation.pptx"
        notes = work / "smoke-speaker-notes.md"
        preview = work / "smoke-preview.png"
        deck_script = work / "deck.js"
        deck_script.write_text(
            """\
const pptxgen = require("pptxgenjs");
const H = require("pptx-helpers");

const TOKENS = {
  palette: { canvas: "FFFFFF", surface: "FFFFFF", primary_text: "111827",
             secondary_text: "4B5563", primary_accent: "2563EB", secondary_accent: "93C5FD" },
  typography: { title_min_pt: 24, body_cjk_min_pt: 22, body_latin_min_pt: 20,
                title_font: "Cambria", body_font: "Calibri" },
  geometry: { safe_margin_pct: 6, title_zone_pct: 16, footer_zone_pct: 5,
              spacing_scale_pt: [6,12,18,24,36,48], corner_radius_pt: 8 },
  lines: { standard_pt: 1.25, emphasis_pt: 2.5 }
};
const LANG = "english";

const pptx = new pptxgen();
H.applyTokens(pptx, TOKENS, LANG);

const AREA = H.safeArea(H.SLIDE_W_IN, H.SLIDE_H_IN, TOKENS);
const slide = pptx.addSlide();
slide.background = { fill: H.color(TOKENS, "canvas") };
H.addTitle(slide, "Claude Code PPTX smoke test", AREA, TOKENS, LANG);
H.addTextBox(slide, "Runtime resolution and delivery validation", {
  x: AREA.x, y: AREA.y + AREA.h * 0.25, w: AREA.w, h: AREA.h * 0.4
}, TOKENS, LANG, { color: H.color(TOKENS, "secondary_text") });

pptx.writeFile({ fileName: process.argv[2] });
""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "node",
                str(ROOT / "scripts/run_with_pptxgenjs.js"),
                "--output",
                str(pptx),
                str(deck_script),
            ],
            check=True,
        )
        validation = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "pptx_tool.py"),
                "validate",
                str(pptx),
                "--json",
                "--output",
                str(work / "smoke-package-report.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if validation.returncode:
            raise SystemExit(
                "Embedded PPTX package validation failed:\n"
                + validation.stdout
                + validation.stderr
            )
        notes.write_text("# Speaker notes\n\nSmoke test.", encoding="utf-8")
        image = Image.new("RGB", (640, 360), "white")
        image.paste((31, 78, 121), (0, 0, 640, 80))
        image.save(preview)
        package_report = work / "smoke-package-report.json"
        if not package_report.is_file():
            raise SystemExit("Generation/validation did not publish a package report.")
        spec = work / "smoke-slide-spec.json"
        spec_report = work / "smoke-slide-spec-report.json"
        spec.write_text(
            json.dumps(
                {
                    "slides": [
                        {
                            "id": 1,
                            "title": "Smoke",
                            "layout": "hero",
                            "kind": "cover",
                            "content": "Smoke",
                            "timing_sec": 30,
                            "owner": "A",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        for script, output in (("validate_slide_spec.py", spec_report),):
            command = [sys.executable, str(ROOT / "scripts" / script), str(spec)]
            command.extend(["--output", str(output), "--json"])
            evidence = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if evidence.returncode:
                raise SystemExit(evidence.stdout + evidence.stderr)
        qa_manifest = work / "smoke-qa-manifest.json"
        delivery_report = work / "smoke-delivery-report.json"
        manifest_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "pptx_tool.py"),
                "qa-manifest",
                "--pptx",
                str(pptx),
                "--preview",
                str(preview),
                "--output",
                str(qa_manifest),
                "--slide-spec-report",
                str(spec_report),
                "--slide-spec",
                str(spec),
                "--package-report",
                str(package_report),
                "--no-repair-needed-reason",
                "Minimal smoke deck inspected after render.",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if manifest_result.returncode:
            raise SystemExit(manifest_result.stdout + manifest_result.stderr)
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "skills/student-presentation-ppt/scripts/pptx_delivery_check.py"),
                "--pptx",
                str(pptx),
                "--notes",
                str(notes),
                "--preview",
                str(preview),
                "--qa-manifest",
                str(qa_manifest),
                "--package-report",
                str(work / "smoke-package-report.json"),
                "--output",
                str(delivery_report),
                "--strict",
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode:
            raise SystemExit(proc.stdout + proc.stderr)
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise SystemExit(
                f"delivery check output is not valid JSON:\n{proc.stdout}\n{proc.stderr}"
            )
        if result.get("slide_count") != 1 or not result.get("ok") or not delivery_report.is_file():
            raise SystemExit(f"Unexpected smoke result: {result}")
        print(json.dumps({"ok": True, "slide_count": 1}, indent=2))


if __name__ == "__main__":
    main()
