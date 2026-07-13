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
            """
const pptxgen = require("pptxgenjs");
const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
const slide = pptx.addSlide();
slide.addText("Claude Code PPTX smoke test", {x: 0.8, y: 0.25, w: 8, h: 0.75, fontSize: 30});
slide.addText("Runtime resolution and delivery validation", {x: 0.8, y: 1.45, w: 8, h: 0.9, fontSize: 22});
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
        image.paste("#1f4e79", (0, 0, 640, 80))
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
        )
        if proc.returncode:
            raise SystemExit(proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        if result.get("slide_count") != 1 or not result.get("ok") or not delivery_report.is_file():
            raise SystemExit(f"Unexpected smoke result: {result}")
        print(json.dumps({"ok": True, "slide_count": 1}, indent=2))


if __name__ == "__main__":
    main()
