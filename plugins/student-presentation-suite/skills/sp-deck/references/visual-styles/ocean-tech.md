# Ocean Tech（海洋科技）

Best for AI, software, engineering, system design, cybersecurity, and future-facing topics.

- **Palette:** `065A82` deep blue dominant, `1C7293` cyan secondary, `21295C` midnight blue for depth.
- **Visual character:** 按页面任务选择架构、流程、截图、代码证据、数据结果或文字主导构图；架构/流程页用 `addArchitecture`/`addProcessFlow` 并就近给出 plain-language takeaway。`primary_accent` `065A82` 与 `secondary_accent` `1C7293` 编码模块层级，正文背景禁用发光。
- **Use when:** AI report, software engineering project, technical architecture, data system, automation, digital transformation.
- **Creative freedom:** architecture diagrams, pipeline flows, code/screenshot annotations, terminal-like evidence panels, dark technical cover, light content slides.
- **Guardrails:** technical neutral base, strict grid alignment; cyan glow is never used behind body text; dark reserved for cover/section.
- **Typography:** technical sans-serif (Arial/Calibri) with monospaced text（等宽仅用 Courier New）只用于 code, commands, IDs, or short evidence snippets; titles clean sans, no decorative strokes.
- **Slide rhythm:** system/problem opening, requirements, architecture or workflow, implementation evidence, test/result, limitations.
- **Charts and diagrams:** architecture maps, pipelines, sequence flows, annotated screenshots, and benchmark comparisons with large labels.
- **Layout motif:** grid alignment, thin connector lines, node cards, module labels, cyan highlight accents.
- **Fallback layout:** when no reliable diagram is available, use one verified implementation artifact or concise system claim with a nearby plain-language takeaway; do not invent architecture detail.
- **Color roles:** light canvas `F4F9FC`; light surface `FFFFFF`; light primary text `132238`; light secondary text `52677A`; light primary accent `065A82`; light secondary accent `1C7293`; dark canvas `21295C`; dark surface `112240`; dark primary text `D6E8FF`; dark secondary text `A3C5D9`; dark primary accent `00C2D1`; dark secondary accent `4E8DFF`.
- **Geometry:** 5-7% margins, minimal corners（`corner_radius_pt`=4，`H.cornerRadius(tokens)`）, strict grid alignment, orthogonal connectors by default, consistent module widths and port spacing.
- **Slide recipes:** signatures = `architecture-layered` and `visual-annotated`; fallback = `process-horizontal`. Expressive intensity is for cover/system overview, standard for architecture and implementation, restrained for benchmarks and limitations. Use 2–6 architecture nodes; split larger systems.
- **Image treatment:** prioritize product screenshots, code/output evidence, architecture diagrams, and real hardware/system context; avoid generic robots, brains, circuits, or neon city art.
- **Density control:** `addArchitecture` supports 2–6 nodes and `addProcessFlow` supports 2–5 steps. Use large labels and one highlighted execution path; split more complex systems into overview/detail pages or use a custom diagram rather than exceeding component limits.
- **Acceptance checks:** a nontechnical audience must identify input, transformation, output, evidence, and limitation; cyan glow is never used behind body text.
- **Do not sacrifice:** readable diagrams, implementation evidence, method/result separation.
- **Avoid:** fake sci-fi glow, tiny architecture labels, decorative circuit backgrounds behind text.
