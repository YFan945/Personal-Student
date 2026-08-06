# Teal Trust（青绿可信）

Best for healthcare, public service, education technology, UX research, and practical improvement proposals.

- **Palette:** neutral light canvas with `028090` teal as the primary accent and `00A896` seafoam as the modeled supporting accent; do not introduce an unmodeled mint role.
- **Visual character:** 用户旅程和服务流页面可用 `addTimeline` 或适配的自定义构图并标明负责方；研究、界面、伦理和结果页按内容选择注释截图、证据或指标。`primary_accent` `028090` 编码用户侧、`secondary_accent` `00A896` 编码系统侧，状态色不超过 3 种。
- **Use when:** medical/public health topic, education platform, user research, service design, policy improvement.
- **Creative freedom:** journey maps, service blueprints, selective persona comparisons, problem-solution flows, annotated interfaces, and restrained icon systems.
- **Guardrails:** restrained teal/mint palette with strong contrast; status colors limited to three; 通常一个主 persona（必要时并排对比 2 个）.
- **Typography:** friendly high-legibility sans-serif body (Arial/Calibri), clear service labels, restrained status colors; titles clean sans, no decorative strokes.
- **Slide rhythm:** user need, current journey/problem, evidence, proposed service flow, feasibility/ethics, expected improvement.
- **Charts and diagrams:** service blueprints, user journeys, annotated interfaces, stakeholder maps, and outcome measures.
- **Layout motif:** rounded but restrained cards, step labels, status chips, annotated screenshots.
- **Fallback layout:** one verified user need beside a responsible actor, proposed intervention, or interface annotation; do not invent a persona or service lane.
- **Color roles:** canvas `F3FAF9`; surface `FFFFFF`; primary text `173B3F`; secondary text `536C70`; primary accent `028090`; secondary accent `00A896`.
- **Geometry:** 6-8% margins, restrained rounded corners（`corner_radius_pt`=10，`H.cornerRadius(tokens)`）, aligned service lanes, consistent status-chip sizes, clear separation between user and system actions.
- **Slide recipes:** signatures = `timeline-roadmap` and `process-horizontal`; fallback = `text-sidebar`. Expressive intensity may open or close a verified service journey; research and ethics pages stay restrained. Complex service blueprints require a custom layout rather than forcing a simple architecture component.
- **Image treatment:** use authentic service contexts, interfaces, touchpoints, and stakeholder evidence; avoid generic medical crosses, smiling-doctor stock, or cute mascot systems.
- **Density control:** `addTimeline` supports 3–6 stages and `addArchitecture` 2–6 nodes; use one primary persona or a genuine two-persona comparison. Complex service-blueprint lanes require a custom composition and must not be forced into `addArchitecture`.
- **Acceptance checks:** user need, intervention, responsible actor, data/privacy boundary, and outcome must be traceable across the deck.
- **Do not sacrifice:** user need, intervention logic, privacy/ethics context when relevant.
- **Avoid:** healthcare clichés, mint-on-white low contrast, overly cute icons.
