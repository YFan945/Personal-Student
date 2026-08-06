# Visual Style Menu

Load `../../../references/shared-standards.md` for typography, readability, and anti-AI consistency. Load `../../../references/image-strategy.md` before choosing photo, generated image, diagram, or fallback visual treatments.

Use these presets as creative directions when the user does not provide a school template or visual direction. Ask the user to choose when visual style materially matters.

Each direction defines intent and guardrails, not a fixed template. The deck may vary layout, cover treatment, section rhythm, chart style, and visual metaphors as long as readability, density, contrast, source safety, and delivery QA remain intact.

Apply constraints in this order: approved school or user template → readability,
source safety, and truthful representation → the slide's narrative job → the selected
style's character → suggested ratios, motifs, and recipes. A lower-priority style
suggestion must never force an unsuitable component or decorative filler.

Interpret the fields consistently:

- `Guardrails` and `Do not sacrifice` contain hard quality boundaries.
- `Visual character`, `Layout motif`, and `Slide recipes` are adaptable defaults.
- `Density control` gives normal ranges; split the slide, change composition, or choose
  another component when the content exceeds them.
- `Fallback layout` is the safe route when suitable imagery, evidence, or structured data
  is unavailable.

## Applying A Style File

Treat the selected style file as executable generation control, not mood-board language:

1. Map its palette roles to actual slide colors: canvas, surface, primary text, secondary text, primary accent, and optional secondary accent.
2. Use its composition and geometry guidance for margins, corner treatment, alignment,
   and visual weight; vary within the safe area when the content needs a better fit.
3. Use its slide-type recipes to vary cover, section, content, data, comparison, process, and closing pages.
4. Follow its image and chart treatment instead of adding generic stock photos or default chart colors.
5. Respect component hard limits and treat style density ranges as defaults. Do not repeat
   one layout more than twice in succession unless a comparison sequence requires it.
6. Run its acceptance checks after rendering. If a style-specific rule conflicts with readability, source safety, a supplied school template, or user instructions, those higher-priority constraints win.

The executable source of style differentiation is `../../../references/design-tokens.json`
under `style_dna`. It defines composition bias, shape/line language, typography treatment,
image treatment, chart grammar, signature motif, preferred layout tags, two signature layouts,
a reliable fallback, and `restrained / standard / expressive` intensity. Use `restrained` on
data, reference, limitation, and dense evidence pages; use `expressive` selectively on covers,
section openings, and closings. Style DNA changes layout ranking and visual treatment only—it
never relaxes capacity, source, contrast, or accessibility rules.

## Shared Executable Layout Library

The 36-layout registry is `layout-library.json`; the runtime API is `../scripts/pptx-layouts.js`:

- `getLayout(id)` returns the declared content contract and normalized zones.
- `selectLayouts(context, tokens, history, count = 3)` filters by content feasibility first,
  then ranks by style DNA, density, and silhouette history with a stable seed.
- `resolveLayout(id, safeArea, options)` maps normalized zones into the current slide safe area.

Slide Spec `layout` remains backward-compatible: a known registry ID is exact intent; a custom
description is mapped by `selectLayouts`. `visual.layout_family` still selects a visual component
family and is not a page-layout identifier. Do not repeat one silhouette for more than two
consecutive slides when another feasible layout exists. Missing images, data, or quotations must
follow the registered fallback rather than creating fake evidence or filler decoration.

Style files use approximate ratios rather than pixel-perfect templates. Interpret `60/40`,
`2/3 + 1/3`, or similar values as starting compositions within the slide safe area; change
them when text length, image crop, chart labels, or template inheritance requires it.

When the user is unsure about style, follow the two-step direction-first flow in `../../../references/presentation-intake.md`: present the four style directions (academic rigorous, business professional, tech modern, creative humanistic), then show the 3–4 best styles in the chosen direction. Add short reasons to the top recommendations, for example: "Academic Rigorous — safest for defense and teacher-facing evaluation" or "Creative Student — better for campus life and product showcase topics." Keep the remaining styles reachable through the "show all 14 styles" shortcut, so the user can still make an informed choice.

## Style Selection Menu

| Style | 中文别名 | Best for | Visual signal | Palette direction |
| --- | --- | --- | --- | --- |
| Academic Rigorous | 学术严谨 | defense, research report, reading report, course design | restrained, evidence-first, formal | navy/charcoal + neutral + one accent |
| Modern Minimal | 现代简洁 | general classroom report, English presentation, concept explanation | clean, spacious, direct | white/gray + bright accent |
| Data Driven | 数据驱动 | survey, experiment, market analysis, comparison | chart-first, KPI-led, evidence-heavy | neutral + blue/green/orange data accents |
| Creative Student | 学生创意 | innovation, campus life, design topic, product idea | vivid, scenario-based, student-like | warm accent + neutral base |
| Midnight Business | 深蓝商务 | business case, entrepreneurship, strategy, management | dark cover, polished corporate rhythm | `1E2761` navy + `CADCFC` ice blue + white |
| Forest Moss | 森林苔藓 | sustainability, agriculture, ecology, health, social good | organic, grounded, calm | `2C5F2D` forest + `97BC62` moss + cream |
| Coral Energy | 珊瑚活力 | marketing, youth topic, campaign, creative proposal | energetic, optimistic, attention-grabbing | `D94E54` coral + `F9E795` gold + navy |
| Warm Terracotta | 暖陶人文 | culture, humanities, community, education reflection | warm, documentary, human-centered | `B85042` terracotta + `F4EEDF` warm canvas + `A7BEAE` sage |
| Ocean Tech | 海洋科技 | software, AI, engineering, systems, future topic | technical, fluid, high-trust | `065A82` deep blue + `1C7293` cyan + `21295C` midnight |
| Charcoal Editorial | 炭黑杂志 | literature, critique, portfolio, serious analysis | magazine-like, monochrome, typographic | `36454F` charcoal + `F2F2F2` off-white + black |
| Teal Trust | 青绿可信 | healthcare, public service, education technology, UX | reliable, clear, friendly | `028090` teal + `00A896` seafoam + neutral surface |
| Berry Cream | 莓果奶油 | psychology, social research, gender/culture, reflective topics | soft, thoughtful, distinctive | `6D2E46` berry + `A26769` dusty rose + `ECE2D0` cream |
| Sage Calm | 鼠尾草平静 | wellness, counseling, learning habits, low-stress reports | quiet, balanced, natural | `4F7F6C` dark sage + `84B59F` soft sage + slate text |
| Cherry Bold | 樱桃醒目 | debate, persuasive pitch, warning/risk, strong conclusion | bold, high-contrast, memorable | `990011` cherry + `FCF6F5` off-white + navy |

## Choosing For An Unsure User

When the user says they are unsure, gives only a topic, or asks "你来定", offer or choose styles this way:
- Defense/research/teacher-scored work: offer `Academic Rigorous`, `Data Driven`, and topic-specific `Ocean Tech` or `Charcoal Editorial`.
- Business/entrepreneurship/project pitch: offer `Midnight Business`, `Data Driven`, and `Coral Energy`.
- AI/software/engineering/system design: offer `Ocean Tech`, `Academic Rigorous`, and `Modern Minimal`.
- Sustainability/health/social good: offer `Forest Moss`, `Teal Trust`, and `Academic Rigorous`.
- Humanities/culture/education reflection: offer `Warm Terracotta`, `Charcoal Editorial`, and `Berry Cream`.
- Campus life/creative/product concept: offer `Creative Student`, `Coral Energy`, and `Modern Minimal`.
- If the grading context is unknown, include at least one conservative option and one expressive option.

When style selection is needed, show the three best topic-fit choices first using the English name and 中文别名, for example `Ocean Tech（海洋科技）`. Show the complete 14-style menu only when the user explicitly asks for all styles. If the user asks the agent to decide, choose one and state why instead of asking again.

## General Visual Principles

- choose a palette that feels specific to the topic instead of defaulting to blue
- map colors by role: neutral canvas/surface for reading, primary and secondary text for
  copy, and accents for emphasis, state, or navigation; do not give every palette color
  equal visual weight
- create clear hierarchy through size, color, spacing, and section rhythm
- repeat one restrained motif at structural moments such as the cover, section openings,
  representative content pages, and close; do not force it onto every slide
- vary layouts across slides instead of repeating the same card grid
- use dark cover/conclusion with lighter content slides when appropriate
- content slides should use a meaningful visual structure when it helps explain, compare,
  evidence, or organize the message; a deliberately composed typography-led slide is valid,
  and no slide should receive filler icons or cards merely to satisfy a visual quota
- avoid decorative underline strokes when they are merely habitual; preserve them when they are part of a supplied template or a deliberate, consistent visual system
- NEVER add decorative color bars, accent stripes, or single-side border bands — these read as AI-generated filler; separate cards with a subtle background tint, drop shadow, or icon instead

## Per-Slide Design Ideas（对齐 document-skills pptx skill）

内容页应选择能解释、比较、举证或组织信息的视觉结构。允许经过设计的文字主导页；
拒绝机械的 title+bullets，也拒绝为了“有视觉”而添加无意义图标、卡片或装饰图。

**布局选项（按页面叙事任务选择，避免连续重复同一轮廓）：**
- 主张主导：大标题/短结论 + 一处证据或限定说明
- 两列：左文字 + 右插图/图表
- 图标 + 文字行：仅在图标确实承担分类或步骤语义时使用
- 2x2 / 2x3 网格：仅用于真实比较或同类信息，不作为默认内容容器
- 半出血图：左或右整侧图片 + 内容覆盖
- 排版主导：短引文、章节命题或关键结论，以字号和留白建立层级

**数据展示：**
- 大数字 callout：60-72pt 大数字 + 下方小标签
- 对比列：before/after、pros/cons、并排选项
- 时间线或流程：编号步骤 + 箭头

**视觉润色：**
- 小节标题旁的小图标仅在其具备识别或导航作用时使用
- 关键统计或标语用斜体点缀
- 一致的圆角图片框、编号块、图标圆作母题，全篇重复

**排版（限安全字体内，见 `pptxgenjs-safety.md` 字体安全表）：**

| 元素 | 字号 |
| --- | --- |
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 中文通常 ≥22pt；英文通常 ≥20pt |
| Captions | 10-12pt muted |

以上为默认目标；共享 design tokens 中的正文和主要标题下限是硬底线。文字不适配时
依次压缩文案、调整容器、更换构图、拆页，不以缩小字号掩盖布局问题。

**间距：**
- 0.5" 最小边距
- 0.3-0.5" 内容块间距
- 留出呼吸空间，不填满每一寸

**Avoid（与 pptx skill 一致）：**
- 不整页重复同一布局；正文不居中（只居中标题）
- 字号对比不足（标题要明显大于正文）
- 默认蓝色；随机间距
- 只给一页上样式、其余裸奔；纯 title+bullets 页
- 忘记文本框内边距（与形状/线条对齐到同一 x 时 `margin: 0`）
- 低对比元素（浅字浅底、深字深底）
- 标题下划线；装饰性色条/强调条/单侧边框（AI 痕迹）
- 未选择暖色风格时默认套用泛化奶油色背景
- 文字溢出容器（减字号/拆页/扩容器，永不裁切）

The 14 style files under `visual-styles/` share one field template (`Palette` →
`Visual character` → `Use when` → `Creative freedom` → `Guardrails` → `Typography` →
`Slide rhythm` → `Charts and diagrams` → `Layout motif` → `Fallback layout` →
`Color roles` → `Geometry` → `Slide recipes` → `Image treatment` → `Density control`
→ `Acceptance checks` → `Do not sacrifice` → `Avoid`). Keep that structure when
editing a style.

## 生成指引（页面类型 → visual family/组件）

生成 deck.js 时按页面类型选 `pptx-visuals.js` 组件（`V.renderVisual` 的 family）；
这是全 deck 统一的映射，各 style 文件的 Slide recipes/Charts 以此为准：

| 页面类型 | visual family | 组件 | 数据要点 |
| --- | --- | --- | --- |
| 封面 | `hero` | addSectionHero | title + takeaway |
| 单图结论 | `dashboard`（带 series） | addChartWithTakeaway | series + takeaway + title |
| KPI 条 | `dashboard`（无 series） | addMetricDashboard | 2-4 个 {value, label} |
| 对比 | `comparison` | addComparison | 2-3 items |
| 流程/步骤 | `process-path` | addProcessFlow | 2-5 steps |
| 时间线 | `timeline` | addTimeline | 3-6 stages |
| 架构/模块 | `architecture` | addArchitecture | 2-6 nodes |
| 矩阵 | `matrix` | addMatrix | 2-4 items |
| 引文 | `quote` | addQuotePanel | quote + source |
| 总结 | `summary` | addSummary | 1-4 takeaways |
| 参考 | `reference` | addReferenceList | items |
| 截图/注释 | `visual-dominant` | addAnnotatedVisual | asset + annotations |

调用方式：`V.renderVisual(slide, family, data, area, tokens, lang)`；图表数据契约见
`pptxgenjs-safety.md` 图表节（takeaway/单位/来源/刻度）。**组件硬上限**：addProcessFlow
2-5 steps、addTimeline 3-6 stages、addMetricDashboard 2-4 metrics、addComparison 2-3 items、
addMatrix 2-4 items、addArchitecture 2-6 nodes——各 style 的 Density control 须对齐这些上限。
这些数字是运行时硬上限；超出时必须拆页、聚合或改用其他构图。
组件库没有的形态（如引文+注释）标注"需手写"，不要硬套近似组件。
小节图标/结论 callout chip 用 `pptx-icons.js`（`I.addIconFromLibrary(slide, name, box, tokens, role)`，
约 30 个：check / warning / info / lightbulb / steps / timeline / user / chart-bar / quote 等，
随 token 着色）。

## Structural Visual Layer

Use visible structural elements only when they organize information or establish hierarchy.
Prefer a flat composition over UI-like panel collections. Do not require a panel, card,
divider, icon, or diagram on every slide.

Use:
- background shape layers to divide sections
- translucent panels behind text only when the selected style and renderer can preserve contrast
- rounded or sharp rectangles as comparison cards, process nodes, and quote blocks
- thin divider lines, numbering blocks, tabs, ribbons, and section markers
- shape callouts for key findings, limitations, Q&A risks, and conclusions
- subtle shadows only when they improve separation without making the slide resemble an app UI

Avoid:
- placing text directly on busy images without a readable panel
- decorative shapes that do not support hierarchy
- low-contrast glass effects
- too many floating cards on one slide
- heavy shadows or effects that make the deck look like a marketing template

**section band 判别规则**（区分合法的 section band 与禁止的装饰性色条）：
- 合法 section band = 与内容区**同宽**的横向色块，色值取 `surface` 或 `secondary_accent`，
  高度 ≥ 一行标题高，用于区分章节/大区块；
- 禁止 = 纵向贴边的窄色条、仅单侧边框、横贯整页的强调条（AI 痕迹）；
- 拿不准时改用背景色块或阴影，不要用色条。

**术语统一**：
- **callout / callout chip / callout pill** 统一为 **callout chip**：圆角小块，填充
  `surface`、边框 `primary_accent`，用于结论/注意点。
- **KPI strips / KPI / big number callout** 统一映射为 `addMetricDashboard` 产出形态
  （2-4 个 {value, label}）。
- **content 页** = 浅色、非封面/章节/引文/参考文献/附录/Q&A 的内容页。
- **比例记法**（30/70、60/40 等）= 基于 safe area 的近似构图指引，可由内容量浮动。

PPTX limitation on glassmorphism: PowerPoint cannot reliably reproduce CSS-style
`backdrop-filter` blur across all apps. Do not use glassmorphism as a general style default.
When an approved direction needs it, simulate it with a restrained translucent layer and
replace it with an opaque panel if contrast or WPS/older PowerPoint rendering is uncertain.

## Template Inheritance

If the user provides a school template:
- preserve logo, footer, school color, and required cover format
- use the template's placeholder structure when it improves consistency
- avoid fighting the template with unrelated palettes
- if placeholders are unclear, keep the school header/footer and rebuild the content area cleanly
