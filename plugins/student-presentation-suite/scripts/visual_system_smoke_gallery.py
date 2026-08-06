#!/usr/bin/env python3
"""Generate 14x8 style, 36-layout, and SVG-atlas visual smoke galleries."""

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
from shared.pptx_static_core import inspect_pptx


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
const S = require('pptx-shapes');
const SVG = require('pptx-svg-library');
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
  H.addTextBox(slide, TOKENS.style_dna.signature_motif, {{x:area.x,y:area.y+area.h*0.56,w:area.w*0.58,h:area.h*0.24}}, tokens, 'chinese', {{fontSize:15,color:H.color(tokens,'secondary_text'),margin:0}});
  H.addStyleMotif(slide, area, tokens, 'expressive');
}}

{{
  const {{ slide, tokens, area }} = baseSlide('light', false);
  SVG.addCornerDecoration(slide, TOKENS.style_dna.corner_svg_set, {{x:area.x,y:area.y+area.h*0.10,w:area.w*0.24,h:area.h*0.62}}, tokens);
  H.addFittedText(slide, '02 证据如何成为结论', {{x:area.x+area.w*0.28,y:area.y+area.h*0.20,w:area.w*0.68,h:area.h*0.34}}, tokens, 'chinese', 'title', {{bold:true,label:'章节标题'}});
  H.addFittedText(slide, TOKENS.style_dna.visual_rhythm, {{x:area.x+area.w*0.30,y:area.y+area.h*0.64,w:area.w*0.50,h:area.h*0.14}}, tokens, 'chinese', 'caption', {{label:'章节节奏'}});
}}

{{
  const {{ slide, tokens, area }} = baseSlide('light', false);
  const stressTitle = '长标题与素材缺失并存时，版式仍须保持清晰';
  const chosen = L.selectLayouts({{slideKind:'content', visualFamily:'visual-dominant', hasAsset:false, title:stressTitle, itemCount:3, seed:TOKENS.style_key}}, TOKENS, [], 1)[0];
  if (!chosen) throw new Error('missing-asset fallback did not produce a feasible layout');
  const zones = L.resolveLayout(chosen.id, area).zones;
  const titleBox = {{...zones.title, h:zones.title.h + area.h*0.060}};
  H.addFittedText(slide, stressTitle, titleBox, tokens, 'chinese', 'title', {{bold:true,label:'长标题 fallback'}});
  const bodyShape = TOKENS.style_dna.shape_grammar[0] === 'arch' ? TOKENS.style_dna.shape_grammar[1] : TOKENS.style_dna.shape_grammar[0];
  S.addStyledContainer(slide, bodyShape, zones.body, tokens, {{fillTransparency:78}});
  const bodyInset = S.safeInsetForShape(bodyShape, zones.body);
  H.addFittedText(slide, '先适配任务与容量，再应用风格。', {{x:zones.body.x+bodyInset.x,y:zones.body.y+bodyInset.y,w:zones.body.w-bodyInset.x*2,h:zones.body.h-bodyInset.y*2}}, tokens, 'chinese', 'body', {{bold:true,max:22,label:'fallback 结论'}});
  SVG.addCornerDecoration(slide, TOKENS.style_dna.corner_svg_set, zones.visual, tokens);
  const noteBox = {{x:area.x+area.w*0.70,y:area.y+area.h*0.84,w:area.w*0.27,h:area.h*0.10}};
  S.addStyledContainer(slide, 'pill', noteBox, tokens, {{fill:H.color(tokens,'surface'),fillTransparency:0,line:H.color(tokens,'secondary_accent')}});
  H.addFittedText(slide, TOKENS.style_dna.fallback_illustration, noteBox, tokens, 'chinese', 'caption', {{align:'center',color:H.color(tokens,'secondary_text'),label:'fallback 说明'}});
}}

{{
  const {{ slide, tokens, area }} = baseSlide('light', true);
  H.addTitle(slide, '缺少照片时使用有解释作用的原创 SVG', area, tokens, 'chinese');
  SVG.addCornerDecoration(slide, TOKENS.style_dna.corner_svg_set, {{x:area.x+area.w*0.06,y:area.y+area.h*0.08,w:area.w*0.38,h:area.h*0.76}}, tokens);
  H.addFittedText(slide, '缺图时改用结构化插图', {{x:area.x+area.w*0.50,y:area.y+area.h*0.20,w:area.w*0.43,h:area.h*0.30}}, tokens, 'chinese', 'body', {{bold:true,label:'SVG 解释'}});
  H.addFittedText(slide, `原创图形：${{TOKENS.style_dna.fallback_illustration}}；不伪装成真实照片。`, {{x:area.x+area.w*0.50,y:area.y+area.h*0.56,w:area.w*0.43,h:area.h*0.20}}, tokens, 'chinese', 'caption', {{label:'SVG 来源说明'}});
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
const V = require('pptx-visuals');
const S = require('pptx-shapes');
const TOKENS = {json.dumps(tokens, ensure_ascii=False)};
const IDS = {json.dumps([item['id'] for item in registry['layouts']], ensure_ascii=False)};
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
H.applyTokens(pptx, TOKENS, 'chinese');

function addCopy(slide, text, box, options = {{}}) {{
  H.addFittedText(slide, text, box, TOKENS, 'chinese', options.textRole || 'body', {{fontSize:options.fontSize || 15,bold:Boolean(options.bold),margin:0.08,color:H.color(TOKENS,options.role || 'primary_text'),align:options.align || 'left',valign:options.valign || 'mid',label:options.label || '版式样例文本'}});
}}

function addPanel(slide, box, label, accent = false, shape = 'roundRect', textRole = 'node') {{
  S.addStyledContainer(slide, shape, box, TOKENS, {{fill:H.color(TOKENS,accent?'secondary_accent':'surface'),fillTransparency:accent?72:4,line:H.color(TOKENS,accent?'primary_accent':'secondary_text')}});
  const inset = S.safeInsetForShape(shape, box);
  addCopy(slide, label, {{x:box.x+inset.x,y:box.y+inset.y,w:box.w-inset.x*2,h:box.h-inset.y*2}}, {{bold:accent,textRole,align:textRole === 'caption' ? 'left' : 'center'}});
}}

function addAbstractVisual(slide, box) {{
  slide.addShape(pptx.ShapeType.rect, {{...box,fill:{{color:H.color(TOKENS,'secondary_accent'),transparency:64}},line:{{color:H.color(TOKENS,'primary_accent'),width:1.2}}}});
  const size = Math.min(box.w, box.h) * 0.28;
  slide.addShape(pptx.ShapeType.ellipse, {{x:box.x+box.w*0.12,y:box.y+box.h*0.18,w:size,h:size,fill:{{color:H.color(TOKENS,'primary_accent'),transparency:12}},line:{{transparency:100}}}});
  slide.addShape(pptx.ShapeType.rect, {{x:box.x+box.w*0.38,y:box.y+box.h*0.45,w:box.w*0.48,h:box.h*0.30,fill:{{color:H.color(TOKENS,'surface'),transparency:8}},line:{{color:H.color(TOKENS,'primary_accent'),width:1}}}});
}}

function renderLayoutSample(slide, layout) {{
  const z = layout.zones;
  const primaryShape = layout.shape_slots[0]?.shape || 'rect';
  if (layout.family === 'cover' || layout.family === 'section') {{
    if (z.body) addCopy(slide, '研究问题：证据如何提升课堂汇报？', z.body, {{bold:true,textRole:'label',align:'center'}});
    if (z.visual) addAbstractVisual(slide, z.visual);
  }} else if (layout.family === 'claim-text') {{
    addPanel(slide, z.body, '结论：完整 QA 后清晰度提升 21 分。', true, primaryShape);
    if (z.visual && layout.id !== 'claim-focus') addPanel(slide, z.visual, '依据：148 页 gallery 完成打包与渲染。');
  }} else if (layout.family === 'visual-image') {{
    addAbstractVisual(slide, z.visual);
    addPanel(slide, z.body, '结构化插图解释关键关系；缺图时不伪造照片。', false, 'pill', 'caption');
  }} else if (layout.family === 'data') {{
    if (layout.id === 'data-kpi-row') {{
      const cells = H.gridLayout(z.visual, 3, 1, {{columnGap:0.12}});
      ['初稿 68','精修 89','提升 +21'].forEach((value,index)=>addPanel(slide,cells[index],value,index===2,['ellipse','pill','hexagon'][index]));
    }} else if (layout.id === 'data-table-highlight') {{
      addPanel(slide, z.visual, '指标      初稿   精修\\n清晰度      68     89\\n证据性      72     91\\n可讲述性    75     88');
    }} else {{
      V.renderVisual(slide, 'dashboard', {{title:'汇报质量评分',takeaway:'完整 QA 后清晰度提升 21 分。',series:[{{name:'评分',labels:['规划','初稿','复核'],values:[68,82,89]}}]}}, z.visual, TOKENS, 'chinese');
    }}
    addCopy(slide, '结论：完整 QA 后，清晰度提升 21 分。', z.body, {{bold:true,textRole:'label',align:'left'}});
  }} else if (layout.family === 'comparison') {{
    if (layout.id === 'compare-criteria') {{
      addPanel(slide, z.body, '维度       固定模板   自适应版式\\n内容适配      弱          强\\n视觉节奏      单一        多样', true);
    }} else {{
      addPanel(slide, z.body, '固定模板\\n生成较快，但长标题和缺图场景容易失衡。', false, primaryShape);
      addPanel(slide, z.visual, '自适应版式\\n先判断容量与素材，再选择构图和视觉 fallback。', true, primaryShape);
    }}
  }} else if (layout.family === 'process-system') {{
    if (layout.id === 'process-vertical') {{
      const cells = H.gridLayout(z.visual, 1, 3, {{rowGap:0.10}});
      ['1 明确结论','2 组织证据','3 渲染复核'].forEach((value,index)=>addPanel(slide,cells[index],value,index===2,layout.shape_slots[index % layout.shape_slots.length]?.shape || 'pill'));
    }} else if (layout.id === 'timeline-roadmap') {{
      const cells = H.gridLayout(z.visual, 4, 1, {{columnGap:0.10}});
      ['1 确认任务','2 选择版式','3 生成页面','4 渲染验收'].forEach((value,index)=>addPanel(slide,cells[index],value,index===3,layout.shape_slots[index % layout.shape_slots.length]?.shape || 'pill'));
    }} else {{
      const family = layout.id === 'architecture-layered' ? 'architecture' : 'process-path';
      const data = family === 'architecture' ? {{nodes:['证据','叙事','页面','复核']}} : {{steps:['结论','证据','页面','复核']}};
      V.renderVisual(slide, family, data, z.visual, TOKENS, 'chinese');
    }}
    if (z.body) addCopy(slide, '步骤标签保持简洁；箭头、编号和空间方向共同表达顺序。', z.body);
  }} else if (layout.id.startsWith('quote-')) {{
    addPanel(slide, z.body, '“设计不是装饰，而是让证据更容易被理解。”\\n— 课堂访谈样例', true);
    if (z.visual && layout.id !== 'quote-focus') addCopy(slide, '解释\\n引文只在有来源且有叙事价值时使用。', z.visual, {{bold:true}});
  }} else if (layout.id === 'references-clean') {{
    V.renderVisual(slide, 'reference', {{references:['教育部（2026）：课堂展示指南','Smith（2025）：Evidence-led Slides','课程访谈记录（2026）']}}, z.body, TOKENS, 'chinese');
    if (z.visual) V.renderVisual(slide, 'reference', {{references:['项目测试报告（2026）','版式 gallery 验收记录（2026）']}}, z.visual, TOKENS, 'chinese');
  }} else {{
    addPanel(slide, z.body, '证据 · 清晰 · 行动', true);
    if (z.visual && !layout.optional_zones.includes('visual')) addCopy(slide, '哪一项证据最能改变判断？', z.visual, {{bold:true,textRole:'label',align:'center'}});
  }}
  addCopy(slide, `${{layout.id}}｜课堂汇报版式`, z.title, {{bold:true,fontSize:18,textRole:'label',align:'left'}});
}}

for (const id of IDS) {{
  const slide = pptx.addSlide();
  H.addBackground(slide, TOKENS);
  const area = H.safeArea(H.SLIDE_W_IN, H.SLIDE_H_IN, TOKENS, {{reserveTitle:true}});
  const layout = L.resolveLayout(id, area);
  renderLayoutSample(slide, layout);
}}
pptx.writeFile({{ fileName: process.argv[2] }});
"""


def svg_atlas_source(tokens: dict[str, object]) -> str:
    return f"""
const pptxgen = require('pptxgenjs');
const H = require('pptx-helpers');
const SVG = require('pptx-svg-library');
const TOKENS = {json.dumps(tokens, ensure_ascii=False)};
const NAMES = Object.keys(SVG.CORNER_SETS);
const pptx = new pptxgen();
H.applyTokens(pptx, TOKENS, 'english');
for (const name of NAMES) {{
  const slide = pptx.addSlide();
  H.addBackground(slide, TOKENS);
  const area = H.safeArea(H.SLIDE_W_IN, H.SLIDE_H_IN, TOKENS, {{reserveTitle:false}});
  SVG.addCornerDecoration(slide, name, {{x:area.x+area.w*0.08,y:area.y+area.h*0.08,w:area.w*0.48,h:area.h*0.78}}, TOKENS);
  H.addFittedText(slide, name, {{x:area.x+area.w*0.58,y:area.y+area.h*0.24,w:area.w*0.40,h:area.h*0.30}}, TOKENS, 'english', 'title', {{bold:true,label:'SVG name'}});
  H.addFittedText(slide, SVG.CORNER_SETS[name], {{x:area.x+area.w*0.58,y:area.y+area.h*0.58,w:area.w*0.36,h:area.h*0.14}}, TOKENS, 'english', 'caption', {{label:'SVG motif'}});
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
    static_result = inspect_pptx(pptx)
    if "error" in static_result:
        raise RuntimeError(f"{name}: static QA failed: {static_result['error']}")
    text_overflow = [
        finding
        for finding in static_result.get("findings", [])
        if "text-vertical-overflow-risk" in finding.get("risk", [])
    ]
    if text_overflow:
        pages = sorted({int(item["slide"]) for item in text_overflow})
        raise RuntimeError(f"{name}: static text overflow risks on pages {pages}")
    previews: list[str] = []
    if render:
        render_dir = target_dir / "render"
        run_checked([sys.executable, str(ROOT / "scripts" / "pptx_tool.py"), "render", str(pptx), "--output-dir", str(render_dir), "--prefix", name], f"{name}: render")
        pages = sorted(render_dir.glob(f"{name}-*.png"))
        if len(pages) != expected_pages:
            raise RuntimeError(f"{name}: expected {expected_pages} rendered pages, got {len(pages)}")
        previews = [str(path) for path in pages]
    return {
        "name": name,
        "pptx": str(pptx),
        "package_report": str(report),
        "previews": previews,
        "static_qa": {
            "finding_count": len(static_result.get("findings", [])),
            "text_overflow_count": 0,
        },
    }


def build_gallery(work: Path, render: bool, gallery: str) -> dict[str, object]:
    from shared.design_tokens import resolve_design_tokens

    catalog = json.loads((ROOT / "references" / "design-tokens.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "skills" / "sp-deck" / "references" / "layout-library.json").read_text(encoding="utf-8"))
    results = []
    if gallery in {"styles", "all"}:
        for style_key in sorted(catalog["styles"]):
            tokens = resolve_design_tokens(style_key)
            results.append(generate_one(work, f"style-{style_key}", style_deck_source(tokens), render, 8))
    if gallery in {"layouts", "all"}:
        tokens = resolve_design_tokens("Modern Minimal")
        results.append(generate_one(work, "layouts-36", layout_deck_source(tokens, registry), render, 36))
    if gallery in {"svg", "all"}:
        tokens = resolve_design_tokens("Modern Minimal")
        results.append(generate_one(work, "svg-atlas-14", svg_atlas_source(tokens), render, 14))
    return {"ok": True, "rendered": render, "gallery": gallery, "artifacts": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate style and shared-layout PPTX galleries")
    parser.add_argument("--gallery", choices=("styles", "layouts", "svg", "all"), default="all")
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
