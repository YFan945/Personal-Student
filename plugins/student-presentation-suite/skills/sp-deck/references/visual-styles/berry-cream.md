# Berry Cream（莓果奶油）

Best for psychology, social research, gender/culture topics, reflective reports, and human behavior.

- **Palette:** `6D2E46` berry dominant, `A26769` dusty rose secondary, `ECE2D0` cream base.
- **Visual character:** 每页必须有“人的观察/引文”作为内容锚点；`primary_accent` `6D2E46` 只用于引文块与 insight 卡片，禁止大面积填充；情感性表述必须紧邻来源标签或 evidence note。
- **Use when:** psychology report, social observation, interview-based research, culture and identity topics.
- **Creative freedom:** quote-led slides, insight cards, participant journey, layered evidence notes, calm contrast charts.
- **Guardrails:** soft rose/berry palette with strong contrast on the cream base; berry accent marks quotes and insights, not decoration.
- **Typography:** rounded or humanist sans-serif body; titles use Cambria/Bookman Old Style for short titles or quotations, body stays Arial/Calibri.
- **Slide rhythm:** warm observation-led cover, participant/context pages, evidence and interpretation, then an honest reflective close.
- **Charts and diagrams:** muted comparison bars, participant journeys, interview-theme clusters, and clearly separated evidence notes.
- **Layout motif:** cream canvases, berry title blocks, soft separators, image/quote pairings; no decorative edge stripes.
- **Fallback layout:** one quotation or observation paired with one interpretation panel; avoid mood-board filler.
- **Color roles:** canvas `ECE2D0`; surface `FFF9F2`; primary text `3B1F2B`; secondary text `75515F`; primary accent `6D2E46`; secondary accent `A26769`.
- **Geometry:** 7-9% margins, soft corners（`corner_radius_pt`=12，`H.cornerRadius(tokens)`）, layered but aligned quote/evidence blocks, 内容块间距用 spacing 档 3–4（18–24pt）、块内 padding ≥16pt.
- **Slide recipes:** cover = human observation + understated title; interview = 约 40/60 quote-to-analysis（35/65–50/50 可浮动）; journey = horizontal stages; comparison = paired participant/context panels.
- **Image treatment:** use respectful portraits only with permission, otherwise hands, environments, artifacts, or abstract human-centered illustrations; avoid beauty-editorial posing.
- **Density control:** one quotation or participant observation per focal area; 通常不超过 3 个 insight clusters（必要时 4 个）; separate evidence from interpretation by color and labels.
- **Acceptance checks:** soft color must not weaken contrast; every emotional statement must be tied to evidence, context, or a clearly marked interpretation.
- **Do not sacrifice:** ethical framing, evidence boundaries, clear conclusions.
- **Avoid:** overly sentimental tone, low-contrast rose text, decorative mood-board slides.

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