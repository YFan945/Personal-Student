# Ocean Tech（海洋科技）

Best for AI, software, engineering, system design, cybersecurity, and future-facing topics.

- **Palette:** `065A82` deep blue dominant, `1C7293` cyan secondary, `21295C` midnight blue for depth.
- **Visual character:** 每页一个系统/流程图（`addArchitecture`/`addProcessFlow`）+ 就近 plain-language takeaway；`primary_accent` `065A82` 与 `secondary_accent` `1C7293` 编码模块层级；正文背景禁用发光。
- **Use when:** AI report, software engineering project, technical architecture, data system, automation, digital transformation.
- **Creative freedom:** architecture diagrams, pipeline flows, code/screenshot annotations, terminal-like evidence panels, dark technical cover, light content slides.
- **Guardrails:** technical neutral base, strict grid alignment; cyan glow is never used behind body text; dark reserved for cover/section.
- **Typography:** technical sans-serif (Arial/Calibri) with monospaced text（等宽仅用 Courier New）只用于 code, commands, IDs, or short evidence snippets; titles clean sans, no decorative strokes.
- **Slide rhythm:** system/problem opening, requirements, architecture or workflow, implementation evidence, test/result, limitations.
- **Charts and diagrams:** architecture maps, pipelines, sequence flows, annotated screenshots, and benchmark comparisons with large labels.
- **Layout motif:** grid alignment, thin connector lines, node cards, module labels, cyan highlight accents.
- **Fallback layout:** one architecture/process diagram with a nearby plain-language takeaway and implementation evidence.
- **Color roles:** light canvas `F4F9FC`; dark canvas `21295C`; surface `FFFFFF`; primary text `132238`; secondary text `52677A`; primary accent `065A82`; secondary accent `1C7293`.
- **Geometry:** 5-7% margins, minimal corners（`corner_radius_pt`=4，`H.cornerRadius(tokens)`）, strict grid alignment, orthogonal connectors by default, consistent module widths and port spacing.
- **Slide recipes:** cover = system claim + architecture fragment; requirement = constraint matrix; architecture = layer/flow map; implementation = screenshot/code evidence; result = benchmark; limitation = boundary/next iteration.
- **Image treatment:** prioritize product screenshots, code/output evidence, architecture diagrams, and real hardware/system context; avoid generic robots, brains, circuits, or neon city art.
- **Density control:** 5-7 nodes per main diagram region, large module labels, one highlighted execution path, and split architecture detail across overview/detail pages.
- **Acceptance checks:** a nontechnical audience must identify input, transformation, output, evidence, and limitation; cyan glow is never used behind body text.
- **Do not sacrifice:** readable diagrams, implementation evidence, method/result separation.
- **Avoid:** fake sci-fi glow, tiny architecture labels, decorative circuit backgrounds behind text.

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