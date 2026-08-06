# Data Driven（数据驱动）

Best for surveys, market analysis, experiments, and comparison-heavy decks.

- **Palette:** neutral base (`F8FAFC` canvas) with blue (`2563EB`) and green (`16A34A`) chart accents defined by `design-tokens.json`; introduce no additional series color without an approved semantic token.
- **Visual character:** 数据发现页应让一个量化结论在 3 秒内可读出：一张主图/表 + 一句 takeaway。背景、方法、定义和限制页可采用来源说明、流程或文字主导构图，不强塞图表；正文和标签使用 `primary_text`/`secondary_text`。
- **Use when:** survey, market analysis, experiment, evaluation, performance comparison, data-backed argument.
- **Creative freedom:** chart-first pages, KPI strips, highlighted evidence panels, before/after comparisons, visual annotations, data-story section openers.
- **Guardrails:** neutral base with the modeled blue/green chart accents, large labels, traceable units/sources, and normally one main chart per finding slide. Add an inset only when it answers the same analytical question.
- **Typography:** tabular numerals where available, bold numeric callouts, plain sans-serif labels (Arial/Calibri), concise chart annotations; titles in a clean serif or sans without decoration.
- **Slide rhythm:** question/hypothesis, data source and method, progressive findings, interpretation, limitations, final evidence-backed conclusion.
- **Charts and diagrams:** choose chart form by comparison task; annotate the takeaway directly and keep scales/source notes visible.
- **Layout motif:** KPI number strips, highlighted evidence panels, chart callout chips, aligned data rows; no decorative bars.
- **Fallback layout:** one chart or table plus a prominent conclusion sentence and compact source/scope note.
- **Color roles:** canvas `F8FAFC`; surface `FFFFFF`; primary text `111827`; secondary text `4B5563`; primary accent `2563EB`; secondary accent `16A34A`.
- **Geometry:** 5-7% margins, square chart areas, aligned numeric baselines, 约 70/30 chart-to-insight layouts（60/40–75/25 可浮动，或直接用 `addChartWithTakeaway` 内置 64/36）, consistent legend placement.
- **Slide recipes:** signatures = `data-chart-sidebar` and `data-small-multiples`; fallback = `data-chart-takeaway`. Analytical pages use standard intensity; methods/limitations are restrained; an expressive overview is allowed only when scales and sources remain explicit. Each chart carries one takeaway.
- **Image treatment:** images are secondary unless they are measured evidence; screenshots and photos require annotation that links them to the quantified result.
- **Density control:** use one analytical question and normally one chart/table per finding slide; directly label up to four series where space permits, otherwise reduce, group, or split. Never use raw spreadsheet screenshots.
- **Acceptance checks:** 每个图表须可溯源（数据源/口径/日期/单位），关键结论标注 takeaway（简单图不强制 baseline）; color meaning must remain consistent across the deck.
- **Do not sacrifice:** data interpretation, source/date/scope notes, readable axes, clear relationship between evidence and claim.
- **Avoid:** raw tables without interpretation, decorative chart junk, unqualified causal claims.
