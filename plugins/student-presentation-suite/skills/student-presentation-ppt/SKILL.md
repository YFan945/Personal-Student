---
name: student-presentation-ppt
description: Use only for a clearly student-owned academic context when the user explicitly asks to create, edit, improve, or rebuild an editable PPT, PPTX, PowerPoint, or slide deck.
version: 0.4.3
---

# Student Presentation PPT

创建或改进可编辑的学生学术 PPTX。仅大纲走 `student-presentation`；只读审查走
`student-presentation-review`；“直接改好”先诊断，再进入本 skill 的编辑分支。

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

状态严格按
`intake_pending → intake_confirmed → planned → producing → qa → complete`
推进，终态为 `incomplete` 或 `blocked`。初始化并持久化状态：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py" init
```

确认前只允许读取用户材料和收集需求，不得检查环境、生成、编辑、渲染或交付。
必须让用户明确批准完整 Production Summary，再调用 `confirm --summary-file <summary>`。

## Workflow

1. 完成完整 intake；用户说“你决定”只表示采用推荐值，仍需展示并确认最终摘要。
2. 确认后运行 `check_claude_pptx_env.py --mode <production_mode> --json --strict`。创建能力缺失或本次编辑能力
   缺失时转 `blocked`；只缺渲染能力可生成候选文件，但最终只能是 `incomplete`。
3. 验证 Presentation Brief 和 Slide Spec，运行 `analyze_presentation_spec.py` 和
   `compile_visual_plan.py`；视觉计划未通过时不写 `deck.js`。生成 production brief，
   并确定唯一 `production_mode`：`create`、`edit_ooxml` 或
   `rebuild_from_source`。转为 `planned`。
4. 转为 `producing`，按 `pptx-production.md` 的对应分支生产。`create` 执行 deck.js；
   `edit_ooxml` 使用 `pptx_tool.py` 解包、结构修改、内容修改、clean、pack；
   `rebuild_from_source` 必须记录明确理由。所有模式都输出新文件，禁止覆盖 source deck。
5. 进入 `qa`，复用生成阶段的 static/package reports，按 `pptx-qa.md` 完成一次渲染、
   逐页视觉、样式和交付检查。首个 candidate 无 blocker 时直接记录无需修复原因；只有
   发现问题并修改 PPTX 后，才重新生成相关证据。
6. 编辑任务生成 change summary 和 revision manifest；版本快照必须传入完整参数。
7. 只有最终 PPTX、static report、预览、QA manifest、package report 和严格 delivery
   report 全部绑定且 blocker 为零时，才可调用
   `workflow_guard.py transition --to complete --pptx <pptx> --qa-manifest <manifest> --package-report <package-report> --delivery-report <report>`。

## Output contract

仅写入 `${CLAUDE_PROJECT_DIR}/outputs` 或当前项目的 `outputs/`：PPTX、speaker notes、
逐页 preview/contact sheet、生成时 static report、QA manifest、style/delivery report，以及编辑任务的 change
summary。中间文件放在 `outputs/.pptx-work/<work-id>/`。最终回复报告所有绝对路径、
页数、package validation、visual QA、交付状态和剩余限制。
