# PPTX Production

本文件只负责生产阶段编排。Intake、内容、证据、图片和视觉标准由共享 canonical
references 负责；低层命令见 `pptx-runtime.md`。

生产前必须具备：已确认的 Production Summary、验证通过的 Presentation Brief 与
Slide Spec、明确的 output prefix、selected visual style，以及唯一 production mode。

## Mode decision

| Mode | 使用条件 | 生产机制 |
| --- | --- | --- |
| `create` | 没有 source deck | pptxgenjs + suite helper |
| `edit_ooxml` | 要保留模板、布局或已有内容 | 解包、结构修改、内容修改、clean、pack |
| `rebuild_from_source` | 原文件损坏或重建更安全，且理由已记录 | 读取原文件后新建，不声称原位编辑 |

`source_deck`、`edit_intent`、`review_findings`、`preserve` 和
`change_summary_required` 是 Slide Spec 顶层字段。存在 source deck 时默认
`edit_ooxml`；不得因为新建更方便而静默改为 rebuild。

## Shared invariants

- 输出和 work directory 必须在项目 `outputs/` 下。
- source deck 只读，生产前后都记录 SHA-256。
- 中文正文不低于 22pt，英文正文不低于 20pt，主要标题不低于 24pt。
- 文本不适配时依次拆页、删减、扩大容器，禁止突破字号下限；溢出靠 QA 逐页视觉检查。
- 坐标必须落在画布内；标题、正文、页脚区与安全边距保持一致。禁止用
  `slideH - 常量` 自算页脚坐标。可用可选 helper 的 `H.safeArea`/`H.gridLayout` 降低
  手算坐标出错率。
- 按 `pptxgenjs-safety.md` 直接写裸 pptxgenjs 脚本；`pptx-helpers.js`/`pptx-visuals.js`
  是可选工具。每页用 `slide.background` 设置背景（canvas 角色），深色封面/浅色内容对比。
- visual plan（`*-visual-plan.json`）是建议性参考，不是门禁；可参考其 layout family 与
  组件建议，但 deck 仍按裸 pptxgenjs 规范写。
- 使用 resolved design tokens；不得另选本 reference 之外的 palette。
- 所有最终 candidate 都必须通过 `pptx_tool.py validate`。

## Create branch

1. 按 Slide Spec 创建 `outputs/.pptx-work/<work-id>/deck.js`。
2. 加载 `pptxgenjs-safety.md`，按官方 gotchas 直接写裸 pptxgenjs 脚本；可用可选
   `require("pptx-helpers")`/`require("pptx-visuals")` 降低算坐标出错率。每页先分
   title/content/footer 三层，再填入内容；每页设 `slide.background`（canvas 角色），
   深色封面/浅色内容对比。不得先写文字后补救坐标。
3. deck.js 从 `process.argv[2]` 接收输出路径；每个输出只创建一个 pptxgen 实例。
4. 执行：

   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/run_with_pptxgenjs.js" --output <candidate.pptx> <deck.js>
   python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" validate <candidate.pptx> \
     --output <candidate-stem>-package-report.json --json
   ```

5. wrapper 在原子落盘前只运行 `normalize-generated`（修复 chart axId/presentation 语义），
   不输出 static report，也不做静态门禁。QA 和 delivery 绑定
   `<candidate-stem>-package-report.json`；文字溢出、重叠、可读性问题由 QA 阶段逐页视觉
   检查发现，修复 generator 后整包重建，禁止对已打包文件做逐项补丁。

## Edit branch

严格按 `pptx-editing.md`：inspect/thumbnail -> unpack -> 所有结构操作 -> 内容/样式修改
-> clean -> pack -> `validate --original --output <package-report>`。不得无条件编写 deck.js，也不得调用会原位覆盖
source 的 vendor CLI。

## Rebuild branch

记录 source hash、无法安全编辑的原因、保留项如何迁移，以及与 edit contract 的差异。
之后执行 create branch，并强制生成 change summary。

## Transition to QA

生产完成只代表获得 candidate。构建 notes/support outputs 后转为 `qa`，再执行
`pptx-qa.md`；此时不得提前对用户声称文件 ready-to-present。
