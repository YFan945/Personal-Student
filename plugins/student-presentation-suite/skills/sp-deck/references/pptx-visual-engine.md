# PPTX Visual Engine

本文件定义 suite-owned 的可执行视觉契约。风格是排序和视觉处理方向，不是逐页固定模板；
内容可行性、可读性、来源和容量约束始终优先。

## Controlled composer

Create/rebuild 默认由 `pptx-composer.js` 统一执行：

- `preflightSlide(slideSpec, context)`：检查标题、正文、素材、容量和 fallback。
- `resolveSlideComposition(slideSpec, context)`：选择 36 个兼容 ID 之一并返回可执行 composition plan。
- `renderSlide(slide, slideSpec, context)`：应用完整 tokens、文字策略、视觉组件和角饰。
- `renderDeck(pptx, slideSpec, context)`：先全 deck preflight，再逐页生成并记录 silhouette 历史。

`deck.js` 只加载已验证的 Slide Spec、resolved tokens、asset manifest，并调用 composer。
自定义 layout 描述由选择器映射到注册表 ID；不得绕开 preflight 手写一套弱化流程。

## Composition and shapes

`pptx-layouts.js` 保留 36 个 ID，并为每个 resolved layout 增加：
`composition`、`shape_slots`、`text_policy`、`asset_slots`、`corner_decoration`、
`variant_fallbacks`。注册表由 `layout-library.schema.json` 校验。

`pptx-shapes.js` 支持 `rect`、`roundRect`、`ellipse`、`pill`、`hexagon`、
`chevron`、`parallelogram`、`arch`、`bracket` 和 `none`。正文安全区必须通过
`safeInsetForShape()` 计算，不能把文字放进尖角。非矩形用于有语义的节点、比较、路径、
焦点和图片框；正文阅读区仍优先使用平面排版。

## SVG library

`pptx-svg-library.js` 提供 `getCornerSvg()`、`getPatternSvg()`、
`addCornerDecoration()`。14 套原创角饰包括 bracket、petal、crop-mark、slash、arc、
tape、axis、contour、beam、focus、circuit、orbit、checkpoint、stamp。SVG 只承担角饰、
背景纹理和确定性辅助插图；正文、数据和主要结构保持 PowerPoint 可编辑。

## Text fit and alignment

使用 `fitText()`、`preflightText()` 和 `addFittedText()`：

- card、node、KPI、短标签：水平居中 + 垂直居中。
- title：按版式左对齐或居中，垂直居中。
- body、list、reference：左对齐；短内容垂直平衡，长内容顶部对齐。
- quote focus 可居中；quote analysis 左对齐。
- caption/source 独立使用 10–12pt，不被正文下限抬高。

无法在角色硬下限内适配时必须阻断，按“扩大区域 → 换变体 → 换版式 → 压缩文案 →
拆页”解决；禁止只告警后交付。

## Style DNA

resolved tokens 必须包含八个可执行维度：`shape_grammar`、`corner_svg_set`、
`component_variants`、`image_frame`、`background_treatment`、
`text_alignment_policy`、`visual_rhythm`、`fallback_illustration`。任意两套标准风格至少
五项不同。Style DNA 只能改变版式排序、形状、角饰、图片处理、组件变体和节奏，不能绕过
来源、对比度、字号、容量或素材许可。

## Assets

默认 `hybrid-adaptive`：优先可靠用户素材；缺图时使用原创 SVG、原生图表、关系图、
时间线或形状结构。禁止空图片框、装饰性 placeholder 和 filler icon。
`<topic>-asset-manifest.json` 必须符合 `references/asset-manifest.schema.json`，记录 slide、
用途、路径、来源、权限、尺寸、裁切、alt text 和 fallback，并通过
`pptx_tool.py validate-asset-manifest`。
