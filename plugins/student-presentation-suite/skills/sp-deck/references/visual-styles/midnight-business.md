# Midnight Business（深蓝商务）

Best for business cases, entrepreneurship, management strategy, and formal project pitches.

- **Palette:** `1E2761` navy dominant, `CADCFC` ice blue secondary, white for clean contrast.
- **Visual character:** 深色封面/章节/结论 + 浅色分析页（`dark_palette.canvas` `1E2761` vs 浅底）；每页一个决策主张 + 三个支撑事实 + 一个启示块；`primary_accent` `CADCFC` 用于关键数字。
- **Use when:** business plan, startup pitch, strategy analysis, management course, competition proposal.
- **Creative freedom:** dark title and closing slides, light analytical content slides, KPI strips, boardroom-style section dividers, crisp comparison cards, strong summary statements.
- **Guardrails:** dark reserved for cover, section, and conclusion; light content pages keep the deck readable; 每页聚焦一个主决策（允许约束/依据句）.
- **Typography:** compact corporate sans-serif (Arial/Calibri) with strong numeric hierarchy; short executive-style titles; restrained emphasis.
- **Slide rhythm:** dark proposition cover, light analysis pages, opportunity/strategy/feasibility, risk, then dark decision summary.
- **Charts and diagrams:** KPI strips, market or competitor comparisons, operating model, financial assumptions, and risk matrix.
- **Layout motif:** top tab or section-number system, large numeric callouts, crisp comparison cards; no decorative left edge band.
- **Fallback layout:** one executive claim, three supporting facts, and one implication block; avoid fake dashboard density.
- **Color roles:** dark canvas `1E2761`; light canvas `F6F8FC`; surface `FFFFFF`; primary dark text `17213C`; light text `FFFFFF`; primary accent `CADCFC`; secondary accent `3B82F6`.
- **Geometry:** 5-7% margins, slightly rounded corners（`corner_radius_pt`=6，`H.cornerRadius(tokens)`）, tab or section-number navigation, disciplined grid, compact numeric spacing.
- **Slide recipes:** cover = proposition + one proof number; market = segment/size/assumption; strategy = choice matrix; operating model = flow; finance = assumptions + trend; close = decision and next step.
- **Image treatment:** prefer product, user, operation, or market evidence; use polished crops and mockups, never anonymous handshakes or skyline stock.
- **Density control:** three KPIs maximum per strip, 每页聚焦一个主决策（允许约束/依据句）, no more than two chart types on a page, and every financial number must expose assumptions.
- **Acceptance checks:** each slide should answer "so what?" for a decision-maker; dark pages are reserved for cover, section, and conclusion rather than the whole deck.
- **Do not sacrifice:** business logic, assumptions, market evidence, risk and financial clarity.
- **Avoid:** glossy fake-corporate decoration, random 3D icons, crowded dashboards, low-contrast blue-on-blue text.

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