#!/usr/bin/env python3
"""Generate the shared-layout and six-page-per-style visual smoke galleries."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from contextlib import nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.pptx_runtime.render import find_pdftoppm, find_soffice


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


def style_deck_source(tokens: dict[str, object]) -> str:
    token_json = json.dumps(tokens, ensure_ascii=False)
    style_label = json.dumps(str(tokens["style_name"]), ensure_ascii=False)
    return f"""
const pptxgen = require('pptxgenjs');
const L = require('pptx-layouts');
const H = require('pptx-helpers');
const V = require('pptx-visuals');
const TOKENS = {token_json};
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
H.applyTokens(pptx, TOKENS, 'chinese');

function baseSlide(mode = 'light', reserveTitle = true) {{
  const tokens = H.paletteMode(TOKENS, mode);
  const slide = pptx.addSlide();
  H.addBackground(slide, tokens);
  const area = H.safeArea(H.SLIDE_W_IN, H.SLIDE_H_IN, tokens, {{ reserveTitle }});
  return {{ slide, tokens, area }};
}}

{{
  const mode = TOKENS.dark_palette ? 'dark' : 'light';
  const {{ slide, tokens, area }} = baseSlide(mode, false);
  H.addTextBox(slide, {style_label}, {{x:area.x,y:area.y+area.h*0.24,w:area.w*0.58,h:area.h*0.24}}, tokens, 'chinese', {{fontSize:34,bold:true,margin:0}});
  H.addTextBox(slide, TOKENS.style_dna.signature_motif, {{x:area.x,y:area.y+area.h*0.58,w:area.w*0.54,h:area.h*0.12}}, tokens, 'chinese', {{fontSize:15,color:H.color(tokens,'secondary_text'),margin:0}});
  H.addStyleMotif(slide, area, tokens, 'expressive');
}}

{{
  const {{ slide, tokens, area }} = baseSlide('light', true);
  H.addTitle(slide, '核心观点：版式必须服从内容', area, tokens, 'chinese');
  const chosen = L.selectLayouts({{slideKind:'content', itemCount:3, seed:TOKENS.style_key}}, TOKENS, [], 1)[0];
  const zones = L.resolveLayout(chosen.id, area).zones;
  H.addTextBox(slide, '先判断叙事任务和容量，再应用风格偏好。', zones.body, tokens, 'chinese', {{bold:true, margin:0}});
  H.addTextBox(slide, `共享版式：${{chosen.id}}`, zones.visual, tokens, 'chinese', {{color:H.color(tokens,'secondary_text'), margin:0}});
}}

{{
  const {{ slide, tokens, area }} = baseSlide('light', true);
  H.addTitle(slide, '参与者证据需要来源与解释', area, tokens, 'chinese');
  V.renderVisual(slide, 'quote', {{quote:'设计不是装饰，而是让证据更容易被理解。', source:'课堂访谈样例（演示数据）'}}, area, tokens, 'chinese');
}}

{{
  const {{ slide, tokens, area }} = baseSlide('light', true);
  H.addTitle(slide, '数据页只突出一个可追溯结论', area, tokens, 'chinese');
  V.renderVisual(slide, 'dashboard', {{title:'方案质量评分', takeaway:'QA 后清晰度提高 21 分。', series:[{{name:'评分', labels:['初稿','精修','QA'], values:[68,84,89]}}]}}, area, tokens, 'chinese');
}}

{{
  const {{ slide, tokens, area }} = baseSlide('light', true);
  H.addTitle(slide, '流程页保持步骤容量与方向清晰', area, tokens, 'chinese');
  V.renderVisual(slide, 'process-path', {{steps:['确认任务','选择版式','生成页面','渲染复核']}}, area, tokens, 'chinese');
}}

{{
  const mode = TOKENS.dark_palette ? 'dark' : 'light';
  const {{ slide, tokens, area }} = baseSlide(mode, true);
  H.addTitle(slide, '以同一视觉系统完成收束', area, tokens, 'chinese');
  V.renderVisual(slide, 'summary', {{takeaways:['风格有差异','版式可适配','QA 决定完成状态']}}, area, tokens, 'chinese');
}}

pptx.writeFile({{ fileName: process.argv[2] }});
"""


def layout_deck_source(tokens: dict[str, object], registry: dict[str, object]) -> str:
    return f"""
const pptxgen = require('pptxgenjs');
const L = require('pptx-layouts');
const H = require('pptx-helpers');
const TOKENS = {json.dumps(tokens, ensure_ascii=False)};
const IDS = {json.dumps([item['id'] for item in registry['layouts']], ensure_ascii=False)};
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
H.applyTokens(pptx, TOKENS, 'english');
for (const id of IDS) {{
  const slide = pptx.addSlide();
  H.addBackground(slide, TOKENS);
  const area = H.safeArea(H.SLIDE_W_IN, H.SLIDE_H_IN, TOKENS, {{reserveTitle:true}});
  const layout = L.resolveLayout(id, area);
  for (const [name, box] of Object.entries(layout.zones)) {{
    slide.addShape(pptx.ShapeType.rect, {{...box, fill:{{color:name==='visual'?H.color(TOKENS,'secondary_accent'):H.color(TOKENS,'surface'), transparency:name==='visual'?62:12}}, line:{{color:H.color(TOKENS,'primary_accent'), width:1}}}});
    H.addTextBox(slide, name, box, TOKENS, 'english', {{fontSize:14, margin:0.08, color:H.color(TOKENS,'primary_text')}});
  }}
  H.addTextBox(slide, `${{id}} · ${{layout.silhouette}} · ${{layout.density}}`, area.titleBox, TOKENS, 'english', {{fontSize:18,bold:true,margin:0}});
}}
pptx.writeFile({{ fileName: process.argv[2] }});
"""


def generate_one(work: Path, name: str, source_text: str, render: bool, expected_pages: int) -> dict[str, object]:
    target_dir = work / name
    target_dir.mkdir(parents=True, exist_ok=True)
    source = target_dir / "gallery.js"
    pptx = target_dir / f"{name}.pptx"
    report = target_dir / "package-report.json"
    source.write_text(source_text, encoding="utf-8")
    run_checked(["node", str(ROOT / "scripts" / "run_with_pptxgenjs.js"), "--output", str(pptx), str(source)], f"{name}: generate")
    run_checked([sys.executable, str(ROOT / "scripts" / "pptx_tool.py"), "validate", str(pptx), "--output", str(report), "--json"], f"{name}: validate")
    previews: list[str] = []
    if render:
        render_dir = target_dir / "render"
        run_checked([sys.executable, str(ROOT / "scripts" / "pptx_tool.py"), "render", str(pptx), "--output-dir", str(render_dir), "--prefix", name], f"{name}: render")
        pages = sorted(render_dir.glob(f"{name}-*.png"))
        if len(pages) != expected_pages:
            raise RuntimeError(f"{name}: expected {expected_pages} rendered pages, got {len(pages)}")
        previews = [str(path) for path in pages]
    return {"name": name, "pptx": str(pptx), "package_report": str(report), "previews": previews}


def build_gallery(work: Path, render: bool, gallery: str) -> dict[str, object]:
    from shared.design_tokens import resolve_design_tokens

    catalog = json.loads((ROOT / "references" / "design-tokens.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "skills" / "sp-deck" / "references" / "layout-library.json").read_text(encoding="utf-8"))
    results = []
    if gallery in {"styles", "all"}:
        for style_key in sorted(catalog["styles"]):
            tokens = resolve_design_tokens(style_key)
            results.append(generate_one(work, f"style-{style_key}", style_deck_source(tokens), render, 6))
    if gallery in {"layouts", "all"}:
        tokens = resolve_design_tokens("Modern Minimal")
        results.append(generate_one(work, "layouts-36", layout_deck_source(tokens, registry), render, 36))
    return {"ok": True, "rendered": render, "gallery": gallery, "artifacts": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate style and shared-layout PPTX galleries")
    parser.add_argument("--gallery", choices=("styles", "layouts", "all"), default="all")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--require-render", action="store_true")
    args = parser.parse_args()
    render_available = bool(find_soffice() and find_pdftoppm())
    if args.require_render and not render_available:
        raise SystemExit("LibreOffice soffice and pdftoppm are required for rendered gallery QA.")
    render = render_available and not args.no_render
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        context = nullcontext(args.output_dir.resolve())
    else:
        context = tempfile.TemporaryDirectory(prefix="sp-visual-system-gallery-")
    with context as location:
        work = Path(location)
        payload = build_gallery(work, render, args.gallery)
        if args.output_dir:
            report_path = work / "gallery-report.json"
            report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            payload["report"] = str(report_path)
        print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
