# Academic Rigorous（学术严谨）

Best for defenses, research reports, reading reports, and teacher-facing coursework.

- **Palette:** dark navy text (`0F172A`) and one restrained blue accent (`1D4ED8`) on a light neutral canvas (`F8FAFC`).
- **Visual character:** 论证、结果和案例页优先呈现“证据 → 结论”关系；按证据类型选择图表、`addAnnotatedVisual` 或自定义证据区，仅在真实比较 2–3 项时使用 `addComparison`。结论可用一处 `primary_accent` callout，标题对齐由页面类型决定，正文通常左对齐。
- **Use when:** defense, research report, reading report, course design, technical or rubric-heavy presentation.
- **Creative freedom:** section bands, annotated screenshots, argument chains, process diagrams, method/result pairing, restrained data emphasis.
- **Guardrails:** dark navy or charcoal with neutral background, one restrained accent, large conservative typography, high contrast, explicit evidence/source boundaries, and no decorative icon filler.
- **Typography:** strong sans-serif titles and compact readable body; use Cambria/Bookman Old Style for short serif quotations only; body stays Arial/Calibri for projection-safe fit.
- **Slide rhythm:** formal cover, question/method section, evidence-heavy content, limitations, then a restrained conclusion/Q&A.
- **Charts and diagrams:** direct labels, thin grid lines, annotated methods/results, no ornamental chart effects.
- **Layout motif:** numbered section markers, thin content dividers, and selective evidence/conclusion pairing; repeat the motif at structural moments instead of forcing it onto every slide.
- **Fallback layout:** when visual evidence is limited, use a clear claim, a compact source or method note, and one qualified conclusion; do not fabricate an evidence panel.
- **Color roles:** canvas `F8FAFC`; surface `FFFFFF`; primary text `0F172A`; secondary text `475569`; primary accent `1D4ED8`; secondary accent `8B9BAB`. Dark cover may invert canvas/text.
- **Geometry:** 6-8% outer margins, square or lightly rounded corners（圆角用 `H.cornerRadius(tokens)`，无 token 时默认）、正文左对齐/标题可居中、thin dividers、结构性/证据面板可用/纯装饰漂浮物不用.
- **Slide recipes:** signatures = `claim-evidence` and `data-chart-takeaway`; fallback = `text-two-column`. Cover/section may be expressive, ordinary evidence uses standard, and references/limitations use restrained intensity. Method may use 约 30/70 label-to-diagram; result may use 约 60/40 chart-to-conclusion, both adjusted to content.
- **Image treatment:** prefer annotated screenshots, source documents, experiment photos, or diagrams; use documentary crops and always keep source/context visible.
- **Density control:** evidence pages usually contain 2–4 evidence units; when a fifth unit or small labels would be required, split the slide or switch to an overview/detail sequence. Tables expose only decision-relevant rows/columns.
- **Acceptance checks:** the thesis, method, evidence, source, and limitation must be distinguishable in a three-second scan; accent color should mark conclusions, not decoration.
- **Do not sacrifice:** source clarity, method/result structure, readable tables/charts, limitation/reflection slides.
- **Avoid:** playful colors, oversized decorative icons, flashy gradients, vague research slogans.
