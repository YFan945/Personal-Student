#!/usr/bin/env python3
"""Generate, render, and strictly validate representative student PPTX scenarios.

Generated artifacts remain in a temporary directory.  CI should invoke this with
``--require-render`` on a runner that has LibreOffice and Poppler installed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_soffice() -> str | None:
    configured = os.environ.get("SOFFICE_PATH")
    candidates = [configured, shutil.which("soffice")]
    if os.name == "nt":
        candidates.extend([
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ])
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def find_pdftoppm() -> str | None:
    candidate = shutil.which("pdftoppm")
    if candidate and Path(candidate).suffix.casefold() in {".cmd", ".bat"}:
        bundled = Path(candidate).parents[2] / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe"
        if bundled.is_file():
            return str(bundled)
    return candidate


def contact_sheet(pages: list[Path], output: Path) -> None:
    images = [Image.open(page).convert("RGB") for page in pages]
    width = max(image.width for image in images)
    height = sum(image.height for image in images)
    sheet = Image.new("RGB", (width, height), "white")
    offset = 0
    for image in images:
        sheet.paste(image, (0, offset))
        offset += image.height
        image.close()
    sheet.save(output)


def run_pdftoppm(pdftoppm: str, pdf: Path, prefix: Path) -> None:
    command = [pdftoppm, "-png", str(pdf), str(prefix)]
    if Path(pdftoppm).suffix.casefold() in {".cmd", ".bat"}:
        command = [os.environ.get("COMSPEC", "cmd.exe"), "/c", *command]
    subprocess.run(command, check=True)


def generate_deck(work: Path, name: str, language: str, roles: list[str]) -> Path:
    deck = work / f"{name}.js"
    pptx = work / f"{name}-presentation.pptx"
    role_json = json.dumps(roles, ensure_ascii=False)
    deck.write_text(f"""
const pptxgen = require('pptxgenjs');
const pptx = new pptxgen(); pptx.layout = 'LAYOUT_WIDE';
const roles = {role_json};
for (const [index, role] of roles.entries()) {{
  const slide = pptx.addSlide(); slide.background = {{ color: 'F8FAFC' }};
  slide.addText(`${{index + 1}}. ${{role}}`, {{x: 0.7, y: 0.25, w: 11.5, h: 0.75, fontSize: 30, bold: true, color: '111827'}});
  slide.addText('Scenario matrix: {language}. This page verifies production, rendering, and delivery gates.', {{x: 0.7, y: 1.45, w: 11.2, h: 1.3, fontSize: 22, color: '4B5563'}});
}}
pptx.writeFile({{ fileName: process.argv[2] }});
""", encoding="utf-8")
    subprocess.run(["node", str(ROOT / "scripts" / "run_with_pptxgenjs.js"), str(deck), str(pptx)], check=True)
    return pptx


def validate_scenario(name: str, scenario: str, language: str, roles: list[str]) -> None:
    data = {
        "meta": {"scenario": scenario, "language": language, "slide_count": len(roles)},
        "slides": [{"id": index + 1, "title": role, "layout": "content", "content": role, "role": role, "timing_sec": 30, "owner": "A"} for index, role in enumerate(roles)],
    }
    errors = semantic_errors(data)
    if errors:
        raise RuntimeError(f"Scenario contract failed for {name}: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run temporary rendered PPTX scenario matrix")
    parser.add_argument("--require-render", action="store_true")
    args = parser.parse_args()
    soffice, pdftoppm = find_soffice(), find_pdftoppm()
    if not soffice or not pdftoppm:
        if args.require_render:
            raise SystemExit("LibreOffice soffice and pdftoppm are required for the render matrix.")
        print(json.dumps({"ok": True, "skipped": True, "reason": "LibreOffice or Poppler unavailable"}))
        return
    delivery = ROOT / "skills" / "student-presentation-ppt" / "scripts" / "pptx_delivery_check.py"
    completed = []
    with tempfile.TemporaryDirectory(prefix="student-presentation-matrix-") as tmp:
        work = Path(tmp)
        for name, (scenario, language, roles) in MATRIX.items():
            validate_scenario(name, scenario, language, roles)
            pptx = generate_deck(work, name, language, roles)
            notes = work / f"{name}-speaker-notes.md"
            notes.write_text("# Matrix notes\n", encoding="utf-8")
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(work), str(pptx)], check=True, capture_output=True, text=True)
            pdf = work / f"{name}-presentation.pdf"
            prefix = work / f"{name}-page"
            run_pdftoppm(pdftoppm, pdf, prefix)
            pages = sorted(work.glob(f"{name}-page-*.png"))
            if len(pages) != len(roles):
                raise RuntimeError(f"{name}: rendered {len(pages)} pages for {len(roles)} slides")
            preview = work / f"{name}-contact.png"
            contact_sheet(pages, preview)
            manifest = work / f"{name}-qa-manifest.json"
            manifest.write_text(json.dumps({
                "pptx_sha256": digest(pptx), "slide_count": len(roles), "rendered_page_count": len(pages), "scenario_contract_passed": True,
                "preview_files": [preview.name], "preview_sha256": [digest(preview)],
                "visual_inspection": {"completed": True, "inspected_pages": list(range(1, len(roles) + 1)), "repair_cycles": 0, "no_repair_needed_reason": "CI rendered scenario baseline.", "remaining_blockers": 0},
            }), encoding="utf-8")
            delivery_result = subprocess.run([sys.executable, str(delivery), "--pptx", str(pptx), "--notes", str(notes), "--preview", str(preview), "--qa-manifest", str(manifest), "--strict", "--json"], check=False, capture_output=True, text=True)
            if delivery_result.returncode:
                raise RuntimeError(f"{name}: strict delivery failed\n{delivery_result.stdout}\n{delivery_result.stderr}")
            completed.append(name)
    print(json.dumps({"ok": True, "rendered_scenarios": completed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
