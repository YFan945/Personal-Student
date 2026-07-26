# pptxgenjs Safety Rules

本文件只保存会影响 PPTX 正确性或跨应用渲染的硬约束；palette、字体尺度和布局由
suite design tokens 决定。

- 添加 slide 前先设置 presentation layout，所有坐标必须落在画布内。
- 颜色使用 6 位十六进制且不含 `#`；透明度使用对应 option，不把 alpha 拼进颜色。
- pptxgenjs 会修改 option object；shadow、fill 等对象不得跨多个 `add*` 调用复用。
- shadow offset 不得为负；需要向上阴影时使用角度。
- 使用 `charSpacing`，不要使用无效的 `letterSpacing`。
- 列表用 rich text item 的 `bullet`，不得在文本中写字面量 `•`。
- 每个输出创建新的 pptxgen instance。
- 文本与几何对齐时显式设置 margin；不得依赖不稳定的自动缩字突破课堂字号下限。
- 标题和正文必须来自同一次 `H.safeArea` 计算；页脚使用 `H.footerArea`，不得自行把
  页脚 y 设为 `slideH - spacing`。多列/多行内容用 `H.gridLayout`；文字使用受控 helper，
  不直接调用 `slide.addText`。
- deck.js 通过 `require("pptx-visuals")` 使用 visual plan 指定的布局组件。组件覆盖
  hero、visual-dominant、process-path、timeline、comparison、dashboard、
  architecture、matrix、quote、summary 和 reference；组件内部生成的 shape、connector、
  chart-like structure 和标注保持可编辑。
- 一个内容页只实现一个主视觉结构。不要在同一页叠放完整流程、长段正文和第二套卡片；
  需要更多解释时拆页或放入 speaker notes。
- Speaker notes 使用 `slide.addNotes()`。
- PowerPoint 原生支持的 chart 必须保持可编辑；组合图的 secondary axes 必须声明完整
  `valAxes` 和 `catAxes`。优先使用 `pptx-visuals.addChartWithTakeaway`；wrapper 的
  generated-package normalization 会清理 PptxGenJS 4.0.1 未声明的二维 series-axis
  reference，但不会替模型补写缺失的数据、单位、来源或结论。
- stacked bar/column 的 data label position 只能使用 PowerPoint 接受的内部位置。
- 不修改 `<p:presentation>` children 顺序。
- `writeFile()` 后必须通过 wrapper 内置的 `static-check`，并调用 suite
  `pptx_tool.py validate`；任一失败都修复 generator 并重建。

这些规则不授权模型绕开 `pptx-helpers.js`。文本 fit、safe area、design tokens 和图片
质量仍由 suite helper、static checker 和 visual QA 共同验证。
