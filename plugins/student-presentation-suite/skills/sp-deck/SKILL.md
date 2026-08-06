---
name: sp-deck
description: Use only for a clearly student-owned academic context when the user explicitly asks to create, edit, improve, or rebuild an editable PPT, PPTX, PowerPoint, or slide deck.
version: 0.5.1
---

# Student Presentation PPT

创建或改进可编辑的学生学术 PPTX。仅大纲走 `sp-outline`；只读审查/诊断走
`sp-review`；编辑请求由 `sp-review` 诊断后以结构化
交接（`outputs/<topic>-slide-spec.yaml`）进入本 skill 的编辑分支。

## Canonical references

- 始终加载 `../../references/presentation-intake.md` 和
  `../../references/shared-standards.md`。
- 规划时加载 `../../references/content-workflow.md`、
  `../../references/slide-spec.md`、`../../references/image-strategy.md` 和
  `references/pptx-production.md`。
- 视觉选择加载 `references/visual-style-menu.md`，确认后只加载一个
  `references/visual-styles/<style>.md`。
- 需要引用时加载 `../../references/evidence-and-citations.md`；编辑或版本控制时加载
  `../../references/revision-training-export.md`。
- 低层命令、安全规则、编辑和 QA 分别由 `references/pptx-runtime.md`、
  `references/pptxgenjs-safety.md`、`references/pptx-editing.md`、
  `references/pptx-qa.md` 负责。

## State gate

状态按
`intake_pending → intake_confirmed → planned → producing → qa → complete`
正向推进，终态为 `incomplete` 或 `blocked`；返工边 `qa → producing` 用于发现问题
后重建，恢复边 `incomplete → qa` 用于补齐缺失门禁后重入 QA，均须带 `--reason <摘要>`。
状态命令统一为：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py" <init | confirm --summary-file <summary> | transition --to <state> [--reason <摘要>]>
# 完成：transition --to complete --pptx <pptx> --qa-manifest <manifest> --delivery-report <report>（见第 7 步）
```

确认前只允许读取用户材料和收集需求，不得检查环境、生成、编辑、渲染或交付。
必须让用户明确批准完整 Production Summary，再调用 `confirm --summary-file <summary>`。

## Workflow

1. **intake**：按 `references/presentation-intake.md` 完成需求收集；展示完整 Production
   Summary 并用 AskUserQuestion 请求确认（确认 / 调整方案 / 更换视觉风格），批准后
   `confirm --summary-file <summary>` 落 `intake_confirmed`。用户说“你决定”只采用推荐值，
   仍须确认摘要。
2. **判定模式**：根据 `source_deck`/`edit_intent` 确定唯一 `production_mode`
   （`create` / `edit_ooxml` / `rebuild_from_source`），规则见 `references/pptx-production.md`。
3. **规划**：验证 Presentation Brief 与 Slide Spec（review 交接分支可跳过 brief，以已确认
   `slide-spec.yaml` 为准），运行 `analyze_presentation_spec.py --strict`；
   `slide_spec_to_pptx_brief.py` 生成 production brief（工具推导并复核 mode）。随后
   `check_claude_pptx_env.py --mode <production_mode> --json --strict`（须在 mode 确定之后）。
   创建/编辑能力缺失 → `blocked`；只缺渲染能力 → 仍可生成，未渲染时按第 7 步处理。
   转为 `planned`。
4. **生产**：转为 `producing`，按 `references/pptx-production.md` 对应分支生成候选
   （create 写 deck.js + helper/visual 组件；edit_ooxml 用 `pptx_tool.py` 解包/修改/clean/pack；
   rebuild 记录理由），产出 `<topic>-package-report.json`，并构建 support outputs：
   讲稿 `<topic>-speaker-notes.md`（从 Slide Spec 的 `speaker_notes`/`note_goal` 逐页导出）、
   预览/contact sheet 与 PDF（渲染产物，可复用 `build_support_outputs.py`）。
   所有模式输出新文件，禁止覆盖 source deck。
5. **QA**：转为 `qa`，按 `references/pptx-qa.md` 顺序：内容 QA（markitdown 提取核对缺页/
   错字/占位符）→ 复用 package report → 渲染+逐页目检（默认必做，单次快循环，只重渲染
   变更页）→ `qa-manifest` → strict delivery check。发现 blocker 无需 reset：
   `transition --to producing --reason <blocker 摘要>` 返工重建后，重跑内容 QA、渲染目检、
   qa-manifest 与 delivery check，再转回 `qa`。
6. **编辑/版本**：编辑任务生成 change summary 与 revision manifest；版本快照传完整参数。
7. **完成**：PPTX、QA manifest、严格 delivery report 全部绑定且 blocker 为零时，
   `transition --to complete --pptx <pptx> --qa-manifest <manifest> --delivery-report <report>`；
   视觉 QA 默认必做，用户明确放弃渲染时可用 `--allow-missing-preview`，未渲染也可 complete（见第 6 节）。

## Output contract

仅写入 `${CLAUDE_PROJECT_DIR}/outputs` 或当前项目的 `outputs/`：PPTX、speaker notes、
逐页 preview/contact sheet、package report、QA manifest、delivery report，以及编辑任务的 change
summary 与 `outputs/<topic>-slide-spec.yaml`（供 review 做 plan-vs-actual）。中间文件放在
`outputs/.pptx-work/<work-id>/`。交付完成后提示用户可运行 `sp-review` 做
只读复核/评分。最终回复报告所有绝对路径、页数、package validation、visual QA、交付状态和剩余限制。
