---
name: student-presentation-ppt
description: Use only for a clearly student-owned academic context when the user explicitly asks to create, edit, improve, or rebuild an editable PPT, PPTX, PowerPoint, or slide deck.
version: 0.5.1
---

# Student Presentation PPT

创建或改进可编辑的学生学术 PPTX。仅大纲走 `student-presentation`；只读审查/诊断走
`student-presentation-review`；编辑请求由 `student-presentation-review` 诊断后以结构化
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
初始化并持久化状态：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py" init
```

确认前只允许读取用户材料和收集需求，不得检查环境、生成、编辑、渲染或交付。
必须让用户明确批准完整 Production Summary，再调用 `confirm --summary-file <summary>`。

## Workflow

1. 完成完整 intake；用户说“你决定”只表示采用推荐值，仍需展示并确认最终摘要。
2. 确认后根据 intake 收集的 `source_deck`/`edit_intent` 确定唯一 `production_mode`
   （`create` / `edit_ooxml` / `rebuild_from_source`），判定规则见 `references/pptx-production.md`。
3. 验证 Presentation Brief 和 Slide Spec（review 编辑交接分支可跳过 brief，以已确认的
   `slide-spec.yaml` 为准），运行 `analyze_presentation_spec.py`；
   `slide_spec_to_pptx_brief.py` 生成 production brief（工具推导并复核 mode，以 intake 的
   `source_deck`/`edit_intent` 为准）。随后运行
   `check_claude_pptx_env.py --mode <production_mode> --json --strict`（env check 必须在
   mode 确定之后）。创建能力缺失或本次编辑能力缺失时转 `blocked`；只缺渲染能力可生成候选文件，
   但未渲染时只能以 `--allow-missing-preview` 交付 `incomplete`。转为 `planned`。
4. 转为 `producing`，按 `references/pptx-production.md` 的对应分支生产。`create` 执行 deck.js；
   `edit_ooxml` 使用 `pptx_tool.py` 解包、结构修改、内容修改、clean、pack；
   `rebuild_from_source` 必须记录明确理由。所有模式都输出新文件，禁止覆盖 source deck。
5. 进入 `qa`，复用生成阶段的 package report，按 `references/pptx-qa.md` 完成交付检查。package
   validation 是强制结构门禁；逐页渲染视觉检查可选（可先在 producing 用 `render` 自检）。
   发现问题时无需重置：`transition --to producing --reason <blocker 摘要>` 返工重建，
   再 `transition --to qa` 重新 qa-manifest 与 delivery check。
6. 编辑任务生成 change summary 和 revision manifest；版本快照必须传入完整参数。
7. 只有最终 PPTX、QA manifest 和严格 delivery report 全部绑定且 blocker 为零时，才可调用
   `workflow_guard.py transition --to complete --pptx <pptx> --qa-manifest <manifest> --delivery-report <report>`。
   预览渲染可选：未渲染时须用 `--allow-missing-preview` 运行 delivery，交付状态为
   `incomplete`（无视觉 QA 证据，不能转 complete）；补渲染后经 `incomplete → qa` 恢复边重入 QA。

## Output contract

仅写入 `${CLAUDE_PROJECT_DIR}/outputs` 或当前项目的 `outputs/`：PPTX、speaker notes、
逐页 preview/contact sheet、package report、QA manifest、delivery report，以及编辑任务的 change
summary 与 `outputs/<topic>-slide-spec.yaml`（供 review 做 plan-vs-actual）。中间文件放在
`outputs/.pptx-work/<work-id>/`。交付完成后提示用户可运行 `student-presentation-review` 做
只读复核/评分。最终回复报告所有绝对路径、页数、package validation、visual QA、交付状态和剩余限制。
