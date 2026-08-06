# Midnight Business（深蓝商务）

Best for business cases, entrepreneurship, management strategy, and formal project pitches.

- **Palette:** light analytical pages use navy text `17213C`, readable blue accent `3157A4`, and white surfaces; dark pages use the complete `dark_palette` with `1E2761` canvas and `CADCFC` ice-blue emphasis.
- **Visual character:** 深色封面/章节/结论 + 浅色分析页；每个决策页聚焦一个结论和 1–3 项最强依据，必要时补一条约束或启示。深色页必须通过 `H.paletteMode(tokens, "dark")` 整体切换文字、表面和强调色，不得只切背景。
- **Use when:** business plan, startup pitch, strategy analysis, management course, competition proposal.
- **Creative freedom:** dark title and closing slides, light analytical content slides, KPI strips, boardroom-style section dividers, crisp comparison cards, strong summary statements.
- **Guardrails:** dark mode is reserved for cover, section, and conclusion; light content pages use the light palette. Avoid fixed evidence counts, fake dashboard density, and unsupported executive claims.
- **Typography:** compact corporate sans-serif (Arial/Calibri) with strong numeric hierarchy; short executive-style titles; restrained emphasis.
- **Slide rhythm:** dark proposition cover, light analysis pages, opportunity/strategy/feasibility, risk, then dark decision summary.
- **Charts and diagrams:** KPI strips, market or competitor comparisons, operating model, financial assumptions, and risk matrix.
- **Layout motif:** top tab or section-number system, large numeric callouts, crisp comparison cards; no decorative left edge band.
- **Fallback layout:** one executive claim with the strongest available 1–3 supporting facts and an optional implication; do not fill space with invented KPIs or dashboard panels.
- **Color roles:** light canvas `F6F8FC`; light surface `FFFFFF`; light primary text `17213C`; light secondary text `52627A`; light primary accent `3157A4`; light secondary accent `3B82F6`; dark canvas `1E2761`; dark surface `17213C`; dark primary text `FFFFFF`; dark secondary text `CBD5E1`; dark primary accent `CADCFC`; dark secondary accent `3B82F6`.
- **Geometry:** 5-7% margins, slightly rounded corners（`corner_radius_pt`=6，`H.cornerRadius(tokens)`）, tab or section-number navigation, disciplined grid, compact numeric spacing.
- **Slide recipes:** signatures = `data-kpi-row` and `claim-evidence`; fallback = `text-sidebar`. Expressive intensity uses the complete dark palette on cover/section/close; analysis stays standard and limitations restrained. KPI rows require real values and finance pages expose assumptions.
- **Image treatment:** prefer product, user, operation, or market evidence; use polished crops and mockups, never anonymous handshakes or skyline stock.
- **Density control:** use 2–4 KPIs only when they support one decision; normally use one chart type per page and a second only when it answers the same question. Split rather than compress, and expose assumptions for every financial number.
- **Acceptance checks:** each slide should answer "so what?" for a decision-maker; dark pages are reserved for cover, section, and conclusion rather than the whole deck.
- **Do not sacrifice:** business logic, assumptions, market evidence, risk and financial clarity.
- **Avoid:** glossy fake-corporate decoration, random 3D icons, crowded dashboards, low-contrast blue-on-blue text.
