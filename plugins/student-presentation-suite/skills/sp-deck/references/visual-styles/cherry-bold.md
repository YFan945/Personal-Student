# Cherry Bold（樱桃醒目）

Best for debates, persuasive pitches, risk warnings, policy arguments, and strong conclusions.

- **Palette:** `990011` cherry dominant, `FCF6F5` off-white secondary, `2F3C7E` navy accent.
- **Visual character:** 每页一个“必须记住的主张”，用大字号标题 + 一个强调数字/风险块；`primary_accent` `990011` 只编码优先级/风险，绝不装饰；其余保持高对比黑白。
- **Use when:** debate, advocacy, warning/risk topic, problem exposure, persuasive recommendation.
- **Creative freedom:** strong opening claim, contrast slides, risk callouts, myth-vs-fact pages, decisive closing slide.
- **Guardrails:** high contrast throughout; red encodes priority/risk only, never decoration; 每页聚焦一个主主张（允许一个限定/依据句）.
- **Typography:** heavy display titles (Cambria/Bookman Old Style) with plain high-legibility body (Arial/Calibri); reserve uppercase and red emphasis for genuinely important claims.
- **Slide rhythm:** provocative claim, evidence and counterargument, risk/choice comparison, recommendation, memorable but qualified close.
- **Charts and diagrams:** high-contrast before/after, risk matrices, myth/fact pairs, and one highlighted threshold or number.
- **Layout motif:** large statement blocks, binary comparison cards, warning callout chips; no decorative edge bands or accent stripes.
- **Fallback layout:** one large claim plus two evidence blocks; avoid filling empty space with warning graphics.
- **Color roles:** canvas `FCF6F5`; surface `FFFFFF`; primary text `182033`; secondary text `5B6475`; primary accent `990011`; secondary accent `2F3C7E`.
- **Geometry:** 6-8% margins, square or slightly rounded blocks（`corner_radius_pt`=8，`H.cornerRadius(tokens)`）, large binary splits, deliberate diagonal 用于封面/章节/关键结论页.
- **Slide recipes:** cover = one provocative but qualified claim; debate = 50/50 claim/counterclaim; risk = severity/likelihood matrix（`addMatrix` 2-4 items）; recommendation = priority stack with one final decision.
- **Image treatment:** prefer evidence images, annotated examples, or symbolic close-ups; use red overlays only to direct attention to a verified problem.
- **Density control:** one warning level per focal block, at most two red-dominant regions per slide, and no more than three competing arguments.
- **Acceptance checks:** red must encode priority or risk consistently; the slide must preserve counterevidence, uncertainty, and non-alarmist language.
- **Do not sacrifice:** nuance, evidence, fairness, non-alarmist wording.
- **Avoid:** sensationalism, all-red slides, using red for every minor point.

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