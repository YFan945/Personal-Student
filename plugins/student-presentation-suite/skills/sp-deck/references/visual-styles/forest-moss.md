# Forest Moss（森林苔藓）

Best for sustainability, agriculture, ecology, public health, and social good topics.

- **Palette:** `2C5F2D` forest green dominant, `97BC62` moss green secondary, cream/off-white backgrounds.
- **Visual character:** 每页一个“实地证据/场景”锚点（图/地图 + 证据面板）；`primary_accent` `2C5F2D` 语义一致地编码主题或状态；正文用暖白底深绿字。
- **Use when:** environmental report, ESG, green campus, food/agriculture, health behavior, community service.
- **Creative freedom:** organic section bands, photo strips, field-note callouts, before/after ecology comparisons, process diagrams with leaf-like soft corners.
- **Guardrails:** green encodes theme or state consistently; warm off-white text fields keep strong contrast; no pale green body text.
- **Typography:** sturdy humanist sans-serif body (Arial/Calibri) with restrained weight changes; titles in Cambria/Bookman Old Style where an organic serif heading fits.
- **Slide rhythm:** place/context opening, evidence of the problem, system or lifecycle explanation, intervention, measured limitations.
- **Charts and diagrams:** lifecycle flows, maps, before/after comparisons, field observations, and practical impact indicators.
- **Layout motif:** soft rectangular panels, subtle texture-like background blocks, map/photo plus evidence pairings.
- **Fallback layout:** evidence photo/map on one side and a grounded finding/recommendation panel on the other.
- **Color roles:** canvas `F7F4E9`; surface `FFFCF4`; primary text `18351F`; secondary text `536454`; primary accent `2C5F2D`; secondary accent `97BC62`.
- **Geometry:** 7-9% margins, soft rectangles（`corner_radius_pt`=12，`H.cornerRadius(tokens)`）, broad horizontal bands, restrained organic curves, no leaf-shaped text boxes.
- **Slide recipes:** cover = place/context image + grounded claim; system = lifecycle or map; evidence = photo/data pair; intervention = before/after process; impact = indicators + limits.
- **Image treatment:** use field photos, maps, materials, communities, or ecosystems with natural color; pair every scenic image with evidence or explanatory context.
- **Density control:** at most one large photo and three evidence callouts; maintain large labels on maps/process diagrams; avoid packing ecological systems into one page.
- **Acceptance checks:** green must encode theme or state consistently; recommendations must identify actor, action, feasibility, and measurable effect.
- **Do not sacrifice:** data source clarity, causal limits, practical recommendations.
- **Avoid:** overusing leaf icons, decorative nature photos without evidence, weak green-on-cream contrast.

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