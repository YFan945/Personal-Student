# Image And Visual Strategy

Use this shared strategy across planning, PPTX production, and review.

## Source Choice

- Use user-provided assets first when they are relevant, clear, and allowed.
- For real people, places, products, historical material, current events, factual charts, and source-sensitive examples, ask whether web search is allowed before using web images.
- For abstract concepts, process explanations, cover mood images, and conceptual scenes, generated visuals or self-drawn diagrams may be used unless the user forbids generation.
- If the user says no network, no generated images, or user-assets only, respect that constraint and use diagrams, shapes, charts, or text-only layouts.

## Built-in Generation Skill（imagegen）

intake 的配图策略默认是 **生图+SVG/原生形状结合**：封面/背景等必要插图用插件可用的内置
生图 skill（`imagegen`，火山方舟 Doubao Seedream）生成，方法链条/结构图/流程图用 SVG 或
原生形状渲染。

- **什么时候用 imagegen**：封面/尾页背景、抽象概念插图、气氛图、需要视觉冲击但无现成素材
  的场景。生图需要联网 + 生图环境，且通常一次一张，注意成本与时间。
- **什么时候用 SVG/原生形状**：结构图、流程图、对比、时间线、架构示意等"确定性视觉"——
  这些用 `pptx-visuals.js` 组件或原生形状渲染，比生图更精确、可编辑、无版权风险。
- **不要用生图画图表/流程图**：数字、刻度、箭头、节点这些由确定性渲染完成，避免幻觉文字。
- 生图 prompt 必须为幻灯片留出文字区域（如封面左侧留白），并按当前视觉样式色板限定配色。
- 生成后可选的配套技能：`imagegen`（生成）→ `mimo-image-understanding`（质检生成的图是否
  符合预期、有无错字）。

## Fallbacks

If no suitable image is available, do not insert unrelated decoration. Prefer:
- process flow
- comparison table
- timeline
- architecture or concept diagram
- shape callout
- icon + short text
- data chart
- translucent panel or structured background layer

## Production Notes

- Images should explain, evidence, or frame the slide's main message.
- Avoid stock-like images that only fill space.
- Text over images needs enough contrast, usually through an opaque or translucent panel.
- Record web image/source URLs in speaker notes or a references slide when appropriate.

## Review Notes

When reviewing an existing deck, flag:
- unclear source or copyright risk
- low-resolution or stretched images
- visuals that do not support the argument
- factual visuals without citation
- busy backgrounds that reduce readability
