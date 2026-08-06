# Charcoal Editorial（炭黑杂志）

Best for literature reviews, critique, portfolios, serious analysis, and argument-led humanities work.

- **Palette:** `36454F` charcoal dominant, `F2F2F2` off-white secondary, black for sharp text.
- **Visual character:** 排版即主视觉：正文 Arial/Calibri、标题 Cambria/Bookman Old Style，层级靠字号/字重而非颜色；每页至多一个强调元素，留白充足。
- **Use when:** reading report, critique, case essay, design portfolio, analysis with strong quotations.
- **Creative freedom:** editorial cover, large quotation slides, asymmetrical columns, image crops, strong whitespace, text hierarchy as the main design.
- **Guardrails:** monochrome with one accent, generous whitespace, typography carries hierarchy, no decorative color bars.
- **Typography:** typography is the primary visual system; pair a disciplined sans-serif body (Arial/Calibri) with a serif or editorial display face (Cambria/Bookman Old Style) for short headings.
- **Slide rhythm:** editorial cover, chapter-like dividers, argument/evidence spreads, annotated quotation pages, decisive final thesis.
- **Charts and diagrams:** monochrome diagrams with one accent, minimal axes, and captions（12–14pt、高对比） rather than dashboard styling.
- **Layout motif:** vertical rules, page-number-like section markers, wide margins, large claim titles.
- **Fallback layout:** asymmetric text/image or claim/evidence spread with generous whitespace.
- **Color roles:** canvas `F2F2F2`; surface `FFFFFF`; primary text `111111`; secondary text `4B5563`; primary accent `36454F`; secondary accent `C9B89B`.
- **Geometry:** 8-10% margins, strong baseline grid, mostly square corners, asymmetric columns（约 35/65–45/55，由内容量定）, page-number markers at a consistent edge.
- **Slide recipes:** cover = oversized title + one cropped artifact; argument = claim/evidence spread; quotation = 60% quote + 40% annotation; section = chapter number + thesis fragment.
- **Image treatment:** use high-quality crops, grayscale or restrained color grading, visible captions, and deliberate negative space; never use multiple unrelated thumbnails.
- **Density control:** one dominant typographic gesture per slide; body copy should remain in short blocks; do not combine large quote, chart, and long analysis on one page.
- **Acceptance checks:** hierarchy must still work in grayscale; quotation, source, and author analysis must be visually unambiguous.
- **Do not sacrifice:** readability, quote/source boundaries, balanced slide density.
- **Avoid:** all-gray monotony, tiny serif body text, decorative title underlines.

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