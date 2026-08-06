# Teal Trust（青绿可信）

Best for healthcare, public service, education technology, UX research, and practical improvement proposals.

- **Palette:** `028090` teal dominant, `00A896` seafoam secondary, `02C39A` mint accent.
- **Visual character:** 每页一个用户旅程/服务流（`addTimeline`/`addArchitecture`）+ 明确负责方；`primary_accent` `028090` 编码用户侧、`secondary_accent` `00A896` 编码系统侧；状态色 ≤3。
- **Use when:** medical/public health topic, education platform, user research, service design, policy improvement.
- **Creative freedom:** journey maps, service blueprints, persona cards, problem-solution flows, clean icon systems.
- **Guardrails:** restrained teal/mint palette with strong contrast; status colors limited to three; 通常一个主 persona（必要时并排对比 2 个）.
- **Typography:** friendly high-legibility sans-serif body (Arial/Calibri), clear service labels, restrained status colors; titles clean sans, no decorative strokes.
- **Slide rhythm:** user need, current journey/problem, evidence, proposed service flow, feasibility/ethics, expected improvement.
- **Charts and diagrams:** service blueprints, user journeys, annotated interfaces, stakeholder maps, and outcome measures.
- **Layout motif:** rounded but restrained cards, step labels, status chips, annotated screenshots.
- **Fallback layout:** user/problem panel beside an improved workflow or interface annotation.
- **Color roles:** canvas `F3FAF9`; surface `FFFFFF`; primary text `173B3F`; secondary text `536C70`; primary accent `028090`; secondary accent `00A896`.
- **Geometry:** 6-8% margins, restrained rounded corners（`corner_radius_pt`=10，`H.cornerRadius(tokens)`）, aligned service lanes, consistent status-chip sizes, clear separation between user and system actions.
- **Slide recipes:** cover = user need + service promise; research = observation/evidence; journey = current pain points; proposal = improved flow; interface = annotated screen; impact = outcome + ethics.
- **Image treatment:** use authentic service contexts, interfaces, touchpoints, and stakeholder evidence; avoid generic medical crosses, smiling-doctor stock, or cute mascot systems.
- **Density control:** 4-6 journey stages, three status colors maximum, 通常一个主 persona（必要时并排对比 2 个）, and no overlapping service-blueprint lanes.
- **Acceptance checks:** user need, intervention, responsible actor, data/privacy boundary, and outcome must be traceable across the deck.
- **Do not sacrifice:** user need, intervention logic, privacy/ethics context when relevant.
- **Avoid:** healthcare clichés, mint-on-white low contrast, overly cute icons.

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