# Warm Terracotta（暖陶人文）

Best for humanities, culture, education reflection, community research, and documentary-style reports.

- **Palette:** `B85042` terracotta dominant, `E7E8D1` sand secondary, `A7BEAE` sage as calm accent.
- **Visual character:** 每页一个“纪实素材/引文”锚点（图框/引文块）+ 独立解释面板；`primary_accent` `B85042` 用于引文与强调、`A7BEAE` 用于平静注释；留白与分隔清晰。
- **Use when:** cultural topic, history report, education reflection, community interview, literature-adjacent classroom report.
- **Creative freedom:** documentary photo frames, quote blocks, timeline strips, chapter-like section openings, annotated artifacts.
- **Guardrails:** warm neutral base with restrained terracotta accent; framed artifacts retain source captions; no decorative edge stripes.
- **Typography:** humanist body (Arial/Calibri) with restrained serif-like display titles (Cambria/Bookman Old Style); keep quotations visually distinct from analysis.
- **Slide rhythm:** artifact/scene opening, historical or social context, evidence and interpretation, comparison, reflective conclusion.
- **Charts and diagrams:** timelines, annotated artifacts, relationship maps, and quote/evidence chains with explicit sources.
- **Layout motif:** framed source images, quote blocks, timeline strips, chapter-like section markers; no decorative side bands.
- **Fallback layout:** framed source image or quotation paired with a clearly separated interpretation panel.
- **Color roles:** canvas `F4EEDF`; surface `FFFDFC`; primary text `3D2C28`; secondary text `6F5B53`; primary accent `B85042`; secondary accent `A7BEAE`.
- **Geometry:** 7-9% margins, framed rectangular images, softly rounded corners（`corner_radius_pt`=8，`H.cornerRadius(tokens)`）, chapter bands, 约 45/55 artifact-to-analysis layouts（40/60–55/45 可浮动）.
- **Slide recipes:** cover = artifact/scene + reflective question; context = timeline/map; source = quotation/image + annotation; argument = evidence chain; comparison = then/now or perspective pair; close = reflection + boundary.
- **Image treatment:** prioritize archival material, community scenes, artifacts, interview environments, and documentary crops; preserve dates, creators, and source captions.
- **Density control:** one primary artifact or quotation, no more than three annotation points, and sufficient separation between historical context and present interpretation.
- **Acceptance checks:** every nostalgic or warm visual must serve an argument; cultural material must retain source, context, and respectful framing.
- **Do not sacrifice:** argument chain, source attribution, respectful tone.
- **Avoid:** scrapbook clutter, nostalgic decoration without purpose, brown/orange overload.

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