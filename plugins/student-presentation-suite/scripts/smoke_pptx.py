#!/usr/bin/env python3
"""Generate and validate a minimal PPTX through the runtime wrapper."""

from __future__ import annotations

import json
import hashlib
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
                title_font: "Aptos Display", body_font: "Aptos" },
  geometry: { safe_margin_pct: 6, title_zone_pct: 16, footer_zone_pct: 5,
              spacing_scale_pt: [6,12,18,24,36,48], corner_radius_pt: 8 },
  lines: { standard_pt: 1.25, emphasis_pt: 2.5 },
  style_adherence: { max_unapproved_srgb_colors: 2, max_font_families: 3 }
};
const LANG = "english";

const pptx = new pptxgen();
H.applyTokens(pptx, TOKENS, LANG);

const AREA = H.safeArea(H.SLIDE_W_IN, H.SLIDE_H_IN, TOKENS);
const slide = pptx.addSlide();
slide.background = { fill: H.color(TOKENS, "canvas") };
H.addTitle(slide, "Claude Code PPTX smoke test", AREA, TOKENS, LANG);
slide.addText("Runtime resolution and delivery validation", {
  x: AREA.x, y: AREA.y + AREA.h * 0.25, w: AREA.w, h: AREA.h * 0.4,
  fontSize: H.fontSizeScale(TOKENS, LANG).body,
  fontFace: H.fontFamily(TOKENS).body,
  color: H.color(TOKENS, "secondary_text")
});

pptx.writeFile({ fileName: process.argv[2] });
""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "node",
                str(ROOT / "scripts/run_with_pptxgenjs.js"),
                str(deck_script),
                str(pptx),
            ],
            check=True,
        )
        notes.write_text("# Speaker notes\n\nSmoke test.", encoding="utf-8")
        image = Image.new("RGB", (640, 360), "white")
        image.paste((31, 78, 121), (0, 0, 640, 80))
        image.save(preview)
        qa_manifest = work / "smoke-qa-manifest.json"
        delivery_report = work / "smoke-delivery-report.json"
        qa_manifest.write_text(
            json.dumps(
                {
                    "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                    "slide_count": 1,
                    "rendered_page_count": 1,
                    "scenario_contract_passed": True,
                    "preview_files": [preview.name],
                    "preview_sha256": [hashlib.sha256(preview.read_bytes()).hexdigest()],
                    "rendered_at": "2026-01-01T00:00:00Z",
                    "visual_inspection": {
                        "completed": True,
                        "inspected_pages": [1],
                        "repair_cycles": 0,
                        "no_repair_needed_reason": "Minimal smoke deck inspected after render.",
                        "remaining_blockers": 0,
                    },
                }
            ),
            encoding="utf-8",
        )
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
