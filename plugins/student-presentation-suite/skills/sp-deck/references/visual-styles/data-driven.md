# Data Driven（数据驱动）

Best for surveys, market analysis, experiments, and comparison-heavy decks.

- **Palette:** neutral base (`F8FAFC` canvas) with blue (`2563EB`) and green (`16A34A`) chart accents, plus an orange exception series.
- **Visual character:** 每页让“一个量化结论”3 秒内可读出：图/表 + 一句 takeaway；`primary_accent` `2563EB` 只标结论与高亮点，正文/标签用 `primary_text`/`secondary_text`。
- **Use when:** survey, market analysis, experiment, evaluation, performance comparison, data-backed argument.
- **Creative freedom:** chart-first pages, KPI strips, highlighted evidence panels, before/after comparisons, visual annotations, data-story section openers.
- **Guardrails:** neutral base with blue/green/orange chart accents, large labels, 通常一页一主图（可配小副图/inset），每页一个结论句.
- **Typography:** tabular numerals where available, bold numeric callouts, plain sans-serif labels (Arial/Calibri), concise chart annotations; titles in a clean serif or sans without decoration.
- **Slide rhythm:** question/hypothesis, data source and method, progressive findings, interpretation, limitations, final evidence-backed conclusion.
- **Charts and diagrams:** choose chart form by comparison task; annotate the takeaway directly and keep scales/source notes visible.
- **Layout motif:** KPI number strips, highlighted evidence panels, chart callout chips, aligned data rows; no decorative bars.
- **Fallback layout:** one chart or table plus a prominent conclusion sentence and compact source/scope note.
- **Color roles:** canvas `F8FAFC`; surface `FFFFFF`; primary text `111827`; secondary text `4B5563`; primary accent `2563EB`; secondary accent `16A34A`.
- **Geometry:** 5-7% margins, square chart areas, aligned numeric baselines, 约 70/30 chart-to-insight layouts（60/40–75/25 可浮动，或直接用 `addChartWithTakeaway` 内置 64/36）, consistent legend placement.
- **Slide recipes:** source/method = sample + scope + caveat; finding = one chart + one takeaway; comparison = synchronized small multiples; summary = three findings + one limitation.
- **Image treatment:** images are secondary unless they are measured evidence; screenshots and photos require annotation that links them to the quantified result.
- **Density control:** one analytical question per slide, normally one chart/table, no more than four series without direct labeling, and no raw spreadsheet screenshots.
- **Acceptance checks:** 每个图表须可溯源（数据源/口径/日期/单位），关键结论标注 takeaway（简单图不强制 baseline）; color meaning must remain consistent across the deck.
- **Do not sacrifice:** data interpretation, source/date/scope notes, readable axes, clear relationship between evidence and claim.
- **Avoid:** raw tables without interpretation, decorative chart junk, unqualified causal claims.

## 通用设计原则（对齐 document-skills pptx skill）

- 本样式是一套 token/recipe；布局与视觉决策遵循 `pptx-production.md` 的 "Visual design"
  节：主导色占 60-70%、默认深色封面/结论页 + 浅色内容页（sandwich，或整体深色高级风；
  **仅定义了 `dark_palette` 的样式强制深色封面/结论**，其余样式深色页需校验对比度）、
  贯穿 deck 的单一母题、安全字体白名单（Arial/Calibri/Cambria/Times New Roman 等）、
  标题 36-44pt（≥token 24pt 下限）、正文 中文 ≥22pt / 英文 ≥20pt（叠加 token 下限）、
  说明/图注 10-12pt、0.5" 最小边距。
- 每个 **content 页**要有视觉元素（图/表/图标/形状）；封面/章节/引文/参考文献/附录/Q&A
  页不强制装饰（对齐 `visual-style-menu.md`）。
- 页面→视觉组件映射见 `visual-style-menu.md` 的"生成指引"表。
- 禁止：标题下划线、装饰性色条/强调条/单侧边框、纯文字 content 页、低对比文字、默认 Aptos。
- 生成时默认用 `H.safeArea` 划分三层 + `V.renderVisual`（按生成指引表选 family）。