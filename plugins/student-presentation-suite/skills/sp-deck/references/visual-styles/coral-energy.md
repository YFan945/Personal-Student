# Coral Energy（珊瑚活力）

Best for marketing, campaign planning, youth culture, communication, and creative proposals.

- **Palette:** neutral warm canvas with coral `D94E54` as the primary emphasis and gold `F9E795` as a non-text supporting accent; values follow `design-tokens.json`.
- **Visual character:** 封面、概念发布、行动和结尾页可突出号召性结论；分析页以证据和可行性为主。`primary_accent` `D94E54` 用于大字号重点或非交互 callout，`F9E795` 只作填充/标记，不承担普通文字。
- **Use when:** marketing plan, social media topic, youth trend, brand campaign, creative event proposal.
- **Creative freedom:** bold covers, campaign mockups, big slogan slides, audience journeys, and selective icon markers; use social-card layouts only when the content is actually a social asset or channel example.
- **Guardrails:** bright accents on a neutral base; coral and gold never carry normal body text; UI-like badges, buttons, and card grids are not default composition devices.
- **Typography:** bold friendly titles (Cambria/Bookman Old Style optional) with clean sans-serif body (Arial/Calibri); short campaign-style callouts; avoid several competing display fonts.
- **Slide rhythm:** energetic cover, audience insight, concept reveal, campaign journey, feasibility/evidence, clear call to action.
- **Charts and diagrams:** audience funnels（`addProcessFlow`）、journey maps（`addTimeline`）、campaign calendars、KPI snapshots（`addMetricDashboard` 2-4 个），标签用 `primary_text`/`secondary_text`。
- **Layout motif:** poster-like titles, selective callouts, split image/content layouts, and occasional diagonal geometry on high-energy milestone slides.
- **Fallback layout:** coral headline block + one mockup/scene + one evidence panel rather than decorative stickers.
- **Color roles:** canvas `FFF9F0`; surface `FFFFFF`; primary text `202A44`; secondary text `5A6478`; primary accent `D94E54`; secondary accent `F9E795` for fills/markers only.
- **Geometry:** 6-8% margins, bold corners（`corner_radius_pt`=14，`H.cornerRadius(tokens)`）, controlled diagonals, 约 60/40 image-content splits（50/50–70/30 可浮动）, callout chips limited to one family.
- **Slide recipes:** signatures = `section-statement` and `timeline-roadmap`; fallback = `text-two-column`. Expressive intensity fits cover, concept reveal, action, and close; evidence/data pages default to restrained. KPI and persona structures appear only with verified values or research.
- **Image treatment:** use campaign mockups, real audience contexts, or generated scenes with a consistent crop and color grade; avoid random lifestyle photography.
- **Density control:** keep one slogan and one supporting sentence per focal region; use bright markers only when they encode channel, stage, or priority, and split rather than building a dense badge grid. Analytical slides stay calmer than cover and concept pages.
- **Acceptance checks:** campaign creativity must connect to audience insight, channel, feasibility, and measurable outcome; gold should remain an accent, not body-text color.
- **Do not sacrifice:** audience insight, campaign logic, message clarity, evidence behind creative claims.
- **Avoid:** too many stickers, low-contrast coral/gold text, entertainment style that looks unserious for grading.
