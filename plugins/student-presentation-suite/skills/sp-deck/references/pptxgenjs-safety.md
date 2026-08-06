# pptxgenjs Generation Rules

本文件是生成 deck.js 的权威约束，对齐官方 pptx skill 的 gotchas。模型直接写裸
pptxgenjs 脚本；`pptx-helpers.js`/`pptx-visuals.js` 是可选工具库，不是必须依赖。
生成后的正确性由 QA 阶段的 `pptx_tool.py validate` 兜底；逐页渲染视觉检查可选，仅在
怀疑布局问题时做。wrapper 只在生成后做 `normalize-generated`（修复类），不做静态门禁。

## 布局与坐标

1. 添加 slide 前先设 `pres.layout`。默认画布 `LAYOUT_16x9` = 10" × 5.625"；
   坐标超出边缘不会被裁剪，只是画不上。需要更宽画布用 `LAYOUT_WIDE`（13.3" × 7.5"）。
2. 坐标必须落在画布内；建议最小边距 0.5"，内容块间距 0.3-0.5" 并保持一致。

## 颜色与透明度

3. 颜色用 6 位 hex，**不带 `#`，不带 8 位 alpha**（`#FF0000` 和 `"00000020"` 都损坏
   文件）。透明度：fill/image 用 `transparency: 0-100`，shadow 用 `opacity: 0.0-1.0`，
   二者不通用。
4. 渐变填充不支持——需要渐变时用渐变图片当背景。

## 对象与阴影

5. pptxgenjs 会**原地修改 option 对象**（首次使用时把值转成 EMU）。绝不跨多个
   `add*` 调用共享同一个 `shadow`/options 对象——每次新建。
6. shadow `offset` 必须 ≥ 0，负数会损坏文件；向上阴影用 `angle: 270` + 正 offset。
7. `letterSpacing` 被静默忽略，真选项是 `charSpacing`。
8. `rectRadius` 只对 `ROUNDED_RECTANGLE` 生效，`RECTANGLE` 上无效。

## 文本与列表

9. 列表：每一项设 `bullet: true`，禁止在文本里写字面量 `•`（会渲染成双子弹）。数组项
   除最后一项外设 `breakLine: true`。段间距用 `paraSpaceAfter`，不要用 `lineSpacing`
   （会产生巨大间隙）。
10. 文本框有内建内边距——文字要与形状/线条/图标对齐到同一 x 时设 `margin: 0`。
11. 字号建议：Slide title 36-44pt bold、Section header 20-24pt bold、Body 14-16pt、
    Captions 10-12pt muted。中文正文不低于 22pt，英文正文不低于 20pt（沿用 suite 下限）。

## 实例与输出

12. 每个输出文件创建一个新的 `new pptxgen()` 实例，绝不复用。
13. `slide.addNotes("...")` 写入演讲者备注（纯文本，每页一次）；绝不放文本框里。

## 图表

14. PowerPoint 原生能画的都用 `addChart()`，保持可编辑；组合图传数组
    `[{type, data, options}]`。
15. 默认 chart 是裸的：必须设 `showTitle` + `title`、`showValue: true` +
    `dataLabelPosition`、`chartColors`（从调色板取），并静默 frame
    （`catAxisLabelColor`/`valAxisLabelColor`、`valGridLine: { color, size }`、
    `catGridLine: { style: "none" }`、单系列 `showLegend: false`）。
16. stacked bar/column 的 `dataLabelPosition` 只能是 `ctr`/`inEnd`/`inBase`；
    `outEnd` 会损坏文件。
17. 组合图用 secondary 轴时必须同时声明 `valAxes` 和 `catAxes` 各两条，否则 PowerPoint
    丢弃该图表。normalize 会移除未声明的 `c:axId`（pptxgenjs 对普通单系列 chart 也会写一个
    多余轴引用，属常规修复）；若模型本意是双轴组合图，`run_with_pptxgenjs.js` 会在生成期
    **报告警提示**（不阻断），须在 generator 里显式声明双轴。库不暴露的原生功能（趋势线、
    误差线）自己算系列或后处理 OOXML，不回落成渲染图片。
18. `writeFile()` 后必须跑 `python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" validate
    <pptx> --output <package-report.json> --json`；报告里命名的 chart/slide 缺陷要修在
    generator 里重建，不是手改打包后的 XML。

## 包结构

19. **永不重排 `<p:presentation>` 的 children 顺序**。pptxgenjs 把
    `<p:notesMasterIdLst>` 写在 `<p:sldIdLst>` 之后、两个 master 指向同一个 theme，
    PowerPoint 读这个顺序没问题；挪动该元素 deck 就打不开了。schema 校验会用临时副本
    重排，盘上文件保持官方顺序。

## 图片与图标

20. 图片走 `addImage({ data: "image/png;base64," + buf.toString("base64") })`——
    前缀必须带。图标默认用内置库 `pptx-icons.js`
    （`I.addIconFromLibrary(slide, name, box, tokens, role)` / `I.iconSVG(name, color)`，
    约 30 个常用矢量图标，`addImage` base64 嵌入、随 token 着色）；自绘
    `addText`/`addShape` 或手写内联 SVG 为后备；不引入外部图标库。库中无合适图标且自绘
    难以保持一致时，按项目临时安装并注明在生产 brief 中。

## 字体安全表（QA 可信）

写进 pptx 的字体由用户机器的 PowerPoint 渲染，QA 用 LibreOffice 会替换字体、宽度可能
不同。为让 QA 的 text-fit 检查可信：

- **安全字体**（QA 宽度一致 + 随 Office 分发）：Arial、Calibri、Cambria、Times New
  Roman、Courier New、Bookman Old Style、Century Schoolbook。正文和任何需要对齐的文本
  用这些。
- **有性格的标题**：安全衬线（Cambria/Bookman Old Style/Century Schoolbook）+ 安全
  无衬线正文（Calibri/Arial），零 QA 风险。
- **QA 不可靠字体**（替换后宽度不同，overflow 检查可能错）：Georgia、Trebuchet MS、
  Impact、Arial Black、Garamond、Consolas、Palatino Linotype、Calibri Light。用户点名
  才用，容器留 ~10% slack，不信任 QA 的 text-fit。
- **绝不默认 Aptos**：Office 2023+ 默认字体在此无 metric 兼容替换、老 Office 又缺失，
  两端都不可靠。

## 设计规范（禁止项）

- 每页要有视觉元素（图/表/图标/形状），拒绝纯 title+bullets 页。
- 深色背景用于封面/总结页，浅色用于内容页（"三明治"结构）；每页用
  `slide.background`（canvas 角色）设置，深色页用 `dark_palette.canvas`。
- 正文左对齐，只居中标题。
- **禁止**：标题下划线、装饰性色条/强调条/单侧边框、默认奶油色背景
  （`F5F5DC` 等）、默认蓝色、低对比文字。
- 一页只实现一个主视觉结构，不叠放完整流程 + 长段正文 + 第二套卡片；需要更多解释拆页
  或放 speaker notes。
- 不要每页重复同一布局；视觉母题选一个（圆角图片框、编号块、图标圆）全篇重复。

## 可选 helper 使用守则

- 可用 `H.safeArea`/`H.gridLayout`/`H.color`/`H.addBackground` 降低算坐标出错率，
  但必须同时满足上述全部 gotchas。
- `H.assertTextFits` 只 `console.warn` 不阻断生成；溢出靠 QA 逐页视觉检查兜底。
- `pptx-visuals.js` 组件（hero/process/timeline/chart 等）可选；用它们也要满足 gotchas。
- 这些规则不授权绕开本文件；helper 内部已对齐官方规范。
