# Academic Rigorous（学术严谨）

Best for defenses, research reports, reading reports, and teacher-facing coursework.

- **Palette:** dark navy text (`0F172A`) and one restrained blue accent (`1D4ED8`) on a light neutral canvas (`F8FAFC`).
- **Visual character:** 每页必须呈现“证据 → 结论”配对：证据面板用 `addComparison`/`addAnnotatedVisual`，结论用 `primary_accent` 单句 callout；标题可居中、正文左对齐；禁止装饰性图标，一切视觉服务于方法/证据/结果。
- **Use when:** defense, research report, reading report, course design, technical or rubric-heavy presentation.
- **Creative freedom:** section bands, annotated screenshots, argument chains, process diagrams, method/result pairing, restrained data emphasis.
- **Guardrails:** dark navy or charcoal with neutral background, one restrained accent, large conservative typography, high contrast.
- **Typography:** strong sans-serif titles and compact readable body; use Cambria/Bookman Old Style for short serif quotations only; body stays Arial/Calibri for projection-safe fit.
- **Slide rhythm:** formal cover, question/method section, evidence-heavy content, limitations, then a restrained conclusion/Q&A.
- **Charts and diagrams:** direct labels, thin grid lines, annotated methods/results, no ornamental chart effects.
- **Layout motif:** numbered tabs or section markers, thin dividers, evidence panels with one conclusion callout; no floating decorative shapes.
- **Fallback layout:** title + evidence panel + one conclusion callout when source material is limited.
- **Color roles:** canvas `F8FAFC`; surface `FFFFFF`; primary text `0F172A`; secondary text `475569`; primary accent `1D4ED8`; secondary accent `8B9BAB`. Dark cover may invert canvas/text.
- **Geometry:** 6-8% outer margins, square or lightly rounded corners（圆角用 `H.cornerRadius(tokens)`，无 token 时默认）、正文左对齐/标题可居中、thin dividers、结构性/证据面板可用/纯装饰漂浮物不用.
- **Slide recipes:** cover = title + course identity + restrained abstract/evidence visual; method = 约 30/70 label-to-diagram（25/75–40/60 可浮动）; result = 约 60/40 chart-to-conclusion（50/50–70/30 可浮动，由内容量定）; limitation = two-column evidence/boundary.
- **Image treatment:** prefer annotated screenshots, source documents, experiment photos, or diagrams; use documentary crops and always keep source/context visible.
- **Density control:** 通常 2-4 个证据单元（内容密集可至 5 个）; tables should expose only decision-relevant rows/columns; split methods or results that need small labels.
- **Acceptance checks:** the thesis, method, evidence, source, and limitation must be distinguishable in a three-second scan; accent color should mark conclusions, not decoration.
- **Do not sacrifice:** source clarity, method/result structure, readable tables/charts, limitation/reflection slides.
- **Avoid:** playful colors, oversized decorative icons, flashy gradients, vague research slogans.

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