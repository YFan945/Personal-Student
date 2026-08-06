# Cherry Bold（樱桃醒目）

Best for debates, persuasive pitches, risk warnings, policy arguments, and strong conclusions.

- **Palette:** `990011` cherry dominant, `FCF6F5` off-white secondary, `2F3C7E` navy accent.
- **Visual character:** 关键论证页突出一个应被记住的主张，可配一个经证据支持的数字或风险块；背景、方法和限定页保持中性。`primary_accent` `990011` 只编码已验证的优先级、风险或关键结论，不作装饰。
- **Use when:** debate, advocacy, warning/risk topic, problem exposure, persuasive recommendation.
- **Creative freedom:** strong opening claim, contrast slides, risk callouts, myth-vs-fact pages, decisive closing slide.
- **Guardrails:** high contrast throughout; red encodes verified priority/risk only; each slide has one primary claim, while evidence and qualification remain visible without sensational framing.
- **Typography:** heavy display titles (Cambria/Bookman Old Style) with plain high-legibility body (Arial/Calibri); reserve uppercase and red emphasis for genuinely important claims.
- **Slide rhythm:** provocative claim, evidence and counterargument, risk/choice comparison, recommendation, memorable but qualified close.
- **Charts and diagrams:** high-contrast before/after, risk matrices, myth/fact pairs, and one highlighted threshold or number.
- **Layout motif:** large statement blocks, binary comparison cards, warning callout chips; no decorative edge bands or accent stripes.
- **Fallback layout:** one large claim plus two evidence blocks; avoid filling empty space with warning graphics.
- **Color roles:** canvas `FCF6F5`; surface `FFFFFF`; primary text `182033`; secondary text `5B6475`; primary accent `990011`; secondary accent `2F3C7E`.
- **Geometry:** 6–8% starting margins, square or slightly rounded blocks (`corner_radius_pt`=8, `H.cornerRadius(tokens)`), and binary splits when the argument is genuinely binary. Use a deliberate diagonal only on a cover, section, or pivotal conclusion when it does not disrupt the grid.
- **Slide recipes:** signatures = `claim-focus` and `compare-before-after`; fallback = `claim-evidence`. Use expressive intensity only for a supported opening/decision, standard for comparison, restrained for method and caveats. Risk matrices use `addMatrix` with 2–4 evidence-backed items.
- **Image treatment:** prefer evidence images, annotated examples, or symbolic close-ups; use red overlays only to direct attention to a verified problem.
- **Density control:** use one warning level per focal block, normally no more than two red-emphasis regions and three competing arguments; split the slide when nuance or evidence would become cramped.
- **Acceptance checks:** red must encode priority or risk consistently; the slide must preserve counterevidence, uncertainty, and non-alarmist language.
- **Do not sacrifice:** nuance, evidence, fairness, non-alarmist wording.
- **Avoid:** sensationalism, all-red slides, using red for every minor point.
