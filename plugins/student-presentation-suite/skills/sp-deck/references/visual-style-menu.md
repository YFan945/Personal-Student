# Visual Style Menu

Visual styles are lightweight references, not templates or layout engines. A selected style may
guide only four things: overall character, six color roles, background treatment, and one optional
SVG motif. It must not choose layouts, shapes, image crops, chart grammar, component variants, or
page rhythm. The AI designs each page from its content and evidence, following
`pptx-production.md`, `pptx-visual-engine.md`, and the shared safety rules.

Apply priorities in this order: approved user or school template → readability, source safety,
and truthful representation → the slide's narrative task → the selected lightweight visual
reference. SVG motifs are optional suggestions and are never inserted automatically.

## Intake Categories

Step A shows exactly three categories plus `Other`. Step B shows all four styles in the selected
category in one question.

| Category | Four available styles |
| --- | --- |
| Academic and professional / 学术与专业类 | Academic Rigorous, Data Driven, Modern Minimal, Charcoal Editorial |
| Business and technology / 商务与科技类 | Midnight Business, Ocean Tech, Teal Trust, Cherry Bold |
| Creative and humanistic / 创意与人文类 | Creative Student, Coral Energy, Forest Moss, Warm Terracotta |
| Other / 其他 | Free user description; the AI completes and confirms the required custom reference |

Do not expose old “show all styles”, cross-category markers, or multi-round style lists. Recommend
the category and then the style that best fit the topic, but keep the final choice with the user.

## Lightweight Reference Contract

Each file under `visual-styles/` has exactly these fields, in this order:

1. `Style character`
2. `Palette`
3. `Background reference`
4. `SVG reference`

Palette roles are `canvas`, `surface`, `primary_text`, `secondary_text`, `primary_accent`, and
`secondary_accent`. Shared typography, sizing, contrast, safe-area, text-fit, source, and QA rules
come from the shared contracts and are not repeated in style files.

## Other / Custom

When the user selects `Other`, set `visual_style: Other` and complete this structure:

```yaml
visual_style_custom:
  style_character: "风格关键词和整体气质"
  palette:
    canvas: "FFFFFF"
    surface: "F5F5F5"
    primary_text: "111111"
    secondary_text: "555555"
    primary_accent: "2563EB"
    secondary_accent: "93C5FD"
  backgrounds:
    cover: "封面背景说明"
    content: "普通内容页背景说明"
    section: "章节页背景说明"
    closing: "结尾页背景说明"
  svg_reference:
    name: "SVG 母题名称或 none"
    usage: "建议使用位置和强度"
```

The AI may infer missing values from the topic, supplied template, and user description, but the
Production Summary must show all four sections before confirmation. An incomplete custom
reference cannot enter `planned`.

## Compatibility

- `Berry Cream` / `berry-cream` resolves to `Warm Terracotta` with a compatibility warning.
- `Sage Calm` / `sage-calm` resolves to `Forest Moss` with a compatibility warning.
- Any other historical unknown style retains its name as `style_character`, uses the Modern
  Minimal safety palette/background reference, and emits a compatibility warning.

## Optional SVG Toolbox

Each formal style points to one recommended SVG name. The model may use, alter, combine, or ignore
it. Do not insert SVG solely to demonstrate the selected style, and do not use an ornamental SVG
as a replacement for evidence, a chart, a diagram, or a meaningful image. `addStyleMotif()` exists
only as an explicit compatibility helper.

## Layout Independence

The 36-layout registry is an inspiration and deterministic-fallback catalog. `suggestLayouts()`
and `selectLayouts()` rank candidates only by slide task, available assets, capacity, density, and
recent silhouette history. Visual style tokens must not affect their order. Known Slide Spec
`layout` values remain hints unless `layout_lock: true` explicitly requests exact resolution.

## Template Inheritance

When the user supplies a school template, preserve its required logo, footer, colors, cover, and
useful placeholders. The template takes priority over a style reference; do not force unrelated
colors, backgrounds, or SVG motifs into it.
