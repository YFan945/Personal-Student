# Modern Minimal（现代简洁）

Best for general classroom reports and English presentations.

- **Palette:** neutral base (`F8FAFC` canvas) with black/gray text and one bright blue accent (`2563EB`).
- **Visual character:** 每页一个焦点对象 + 一条简洁解释（`addSectionHero`/`addComparison`/`addProcessFlow`）；`primary_accent` `2563EB` 只标一个强调点，其余黑白灰；大留白。
- **Use when:** general classroom report, English presentation, topic introduction, conceptual explanation.
- **Creative freedom:** large claim titles, asymmetrical two-column pages, sparse callouts, simple icons, one strong image per section, restrained translucent panels.
- **Guardrails:** neutral base, black/gray text, one bright accent, simple sans-serif typography, generous spacing.
- **Typography:** one sans-serif family (Arial/Calibri) with clear weight hierarchy; use scale and whitespace instead of extra decoration; titles stay clean sans with no underline decoration.
- **Slide rhythm:** simple cover, alternating text/visual and comparison pages, occasional full-width statement, concise close.
- **Charts and diagrams:** minimal axes, direct labels, simple process lines, and one highlighted conclusion.
- **Layout motif:** asymmetrical two-column pages, simple icons, whitespace zones, one alignment axis per composition.
- **Fallback layout:** asymmetric two-column composition with one focal object and one concise explanation.
- **Color roles:** canvas `F8FAFC`; surface `FFFFFF`; primary text `111827`; secondary text `6B7280`; primary accent `2563EB`; secondary accent `93C5FD`.
- **Geometry:** 8-10% margins, mostly square or slightly rounded corners（`corner_radius_pt`=8，`H.cornerRadius(tokens)`）, 约 60/40 asymmetric columns（50/50–65/35 可浮动）, large whitespace zones, one alignment axis per composition.
- **Slide recipes:** cover = short title + one focal visual; concept = statement + diagram; comparison = clean two-column; process = 3-5 numbered steps; close = one takeaway + Q&A cue.
- **Image treatment:** one strong image per section or one diagram per content page; use consistent crop ratios and avoid icon collections used as filler.
- **Density control:** 2-4 content units, one accent region, 不连续重复同一构图超过 2 次（对比序列除外）, and 避免大段正文；必要时用 2-3 行短段 + 要点.
- **Acceptance checks:** remove any element that does not change comprehension; whitespace must frame a real focal point rather than leave the slide unfinished.
- **Do not sacrifice:** audience-appropriate speakability, short slide text, projection contrast, natural speaker notes.
- **Avoid:** dense tables, visual clutter, repeated cards on every slide, decorative minimalism that leaves slides empty.

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