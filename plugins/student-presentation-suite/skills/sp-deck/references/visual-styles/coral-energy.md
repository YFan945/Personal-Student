# Coral Energy（珊瑚活力）

Best for marketing, campaign planning, youth culture, communication, and creative proposals.

- **Palette:** `F96167` coral dominant, `F9E795` gold secondary（accents only，色值以 design-tokens.json 为准）.
- **Visual character:** 每页一个“号召性结论”：`primary_accent` `F96167` 用于标题/关键按钮，`F9E795` 只做强调；每页最多 3 个亮色 badge，分析页比封面克制。
- **Use when:** marketing plan, social media topic, youth trend, brand campaign, creative event proposal.
- **Creative freedom:** bold covers, campaign mockups, social-card layouts, big slogan slides, audience journey, bright icon badges.
- **Guardrails:** bright accents on a neutral base; gold stays an accent, never body-text color; at most three bright badges.
- **Typography:** bold friendly titles (Cambria/Bookman Old Style optional) with clean sans-serif body (Arial/Calibri); short campaign-style callouts; avoid several competing display fonts.
- **Slide rhythm:** energetic cover, audience insight, concept reveal, campaign journey, feasibility/evidence, clear call to action.
- **Charts and diagrams:** audience funnels（`addProcessFlow`）、journey maps（`addTimeline`）、campaign calendars、KPI snapshots（`addMetricDashboard` 2-4 个），标签用 `primary_text`/`secondary_text`。
- **Layout motif:** diagonal blocks, poster-like titles, vivid callout chips used sparingly, split image/content layouts.
- **Fallback layout:** coral headline block + one mockup/scene + one evidence panel rather than decorative stickers.
- **Color roles:** canvas `FFF9F0`; surface `FFFFFF`; primary text `202A44`; secondary text `5A6478`; primary accent `F96167`; secondary accent `F9E795`.
- **Geometry:** 6-8% margins, bold corners（`corner_radius_pt`=14，`H.cornerRadius(tokens)`）, controlled diagonals, 约 60/40 image-content splits（50/50–70/30 可浮动）, callout chips limited to one family.
- **Slide recipes:** cover = campaign statement + hero mockup; audience = persona/journey; concept = one big idea + three proof points; rollout = calendar/path; KPI = three-number strip.
- **Image treatment:** use campaign mockups, real audience contexts, or generated scenes with a consistent crop and color grade; avoid random lifestyle photography.
- **Density control:** one slogan and one supporting sentence per focal region; at most three bright badges; keep analytical slides calmer than cover and concept pages.
- **Acceptance checks:** campaign creativity must connect to audience insight, channel, feasibility, and measurable outcome; gold should remain an accent, not body-text color.
- **Do not sacrifice:** audience insight, campaign logic, message clarity, evidence behind creative claims.
- **Avoid:** too many stickers, low-contrast coral/gold text, entertainment style that looks unserious for grading.

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