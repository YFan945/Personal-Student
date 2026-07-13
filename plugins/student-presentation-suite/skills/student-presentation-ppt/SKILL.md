---
name: student-presentation-ppt
description: Use only for a clearly student-owned academic context when the user explicitly asks to create, edit, improve, or rebuild an editable PPT, PPTX, PowerPoint, or slide deck.
---

# Student Presentation PPT

创建或改进实际可编辑的学生演示文稿。

## 快速约束

- 中文正文 ≥ 22pt / 英文正文 ≥ 20pt / 标题 ≥ 24pt
- **文字适配优先级**：确保文本框能装下文字 > 保持最小字号。文字装不下时，优先拆分幻灯片或删减内容，不得将字号缩小到最小值以下
- 预估公式：中文字宽 ≈ 字号×0.035cm，英文 ≈ 字号×0.021cm；行高 ≈ 字号×1.4；每行字符数 = 盒宽÷字宽；所需行数 = 总字符数÷每行字符数；文字总高 = 所需行数×行高。文字总高超过盒高 85% 时存在溢出风险
- 每页一条核心信息，≤ 4 条要点，≤ 80 中文字 / 40 英文词
- 避免 AI 套话（"在当今快速发展..."、"具有重要意义..."）；用课程/项目具体细节替代
- 按目录→逐页主张→PPT文案→演讲版→Slide Spec 分层生成
- 生成前必须确认完整 Production Summary（18 项）— 用户说"你决定"只填充推荐值，不跳过确认
- 状态机：`intake_pending → intake_confirmed → planned → producing → qa → complete`
- 输出写入 `${CLAUDE_PROJECT_DIR}/outputs`，不得覆盖源文件
- PPTX 生产依赖 `document-skills@anthropic-agent-skills`

## 职责

- 创建/改进可编辑 PPTX → 本 skill
- 仅大纲 → `student-presentation`
- 审查已有文件 → `student-presentation-review`
- "直接改好" → 先诊断，再在本 skill 中编辑，输出独立改进版 + change summary

## 状态门禁

加载 `../../references/presentation-intake.md`，使用完整 PPTX intake。

用 `workflow_guard.py init` 初始化项目状态。保存完整 Production Summary 到 `outputs/`；只有明确批准后运行 `workflow_guard.py confirm --summary-file <摘要>`。`PreToolUse` hook 在确认前阻断生产脚本。

状态卡住时使用 `workflow_guard.py reset` 重置，使用 `workflow_guard.py unblock` 从 blocked 回到 `intake_pending` 并重新确认摘要。`complete` 只能通过携带当前 PPTX 的 `--qa-manifest` 和 `--pptx` 的状态转换获得。

## 工作流

1. 完成 intake 并获得明确确认。
2. 按需加载：
   - `../../references/presentation-brief.md` — 场景/受众/质量/控制
   - `../../references/content-workflow.md` — 分层生成与故事检查
   - `../../references/evidence-and-citations.md` — 证据与引用
   - `../../references/revision-training-export.md` — 锁定/修订/导出
   - `references/pptx-production.md` — 生产机制
   - `references/visual-style-menu.md` → 一份 `references/visual-styles/<style>.md`
   - `../../references/slide-spec.md` — 结构化交接
   - `../../references/image-strategy.md` — 视觉素材策略
3. 验证确认的 Presentation Brief。创建分层内容和经过验证的 Slide Spec v2；运行 `analyze_presentation_spec.py`；将工作流状态转为 `planned`。
4. 运行 `python "${CLAUDE_PLUGIN_ROOT}/scripts/check_claude_pptx_env.py" --json --strict`。必需工具缺失时 `blocked`（node/pptxgenjs/markitdown/Pillow/document-skills）；LibreOffice/Poppler 缺失仅警告。
5. 对 Slide Spec 输入运行 `slide_spec_to_pptx_brief.py` 生成 Claude pptx brief。
6. 转为 `producing`，遵循 `document-skills` 的 `pptx` skill：新建 → `pptxgenjs.md`，编辑 → `editing.md`。
7. 生成的 Node 脚本通过 `run_with_pptxgenjs.js` 运行。
8. 用 `build_support_outputs.py` 构建辅助输出。转为 `qa`；运行文本提取、渲染、视觉检查、质量报告、至少一次修复-验证循环，写入带 PPTX/preview hash、页数、检查页和 blocker 数的 `qa-manifest.json`。用 `style_adherence_check.py --pptx <pptx> --visual-style <style> --output <style-report> --strict` 检查 token 一致性，再运行 `pptx_delivery_check.py --qa-manifest <manifest> --style-report <style-report> --strict --json`。编辑时运行 `create_revision_manifest.py --strict`。用 `manage_versions.py` 做版本快照。所有门禁通过后用 `workflow_guard.py transition --to complete --pptx <pptx> --qa-manifest <manifest>` 完成状态转换。

## 输出契约

仅写入 `${CLAUDE_PROJECT_DIR}/outputs`（无此变量时用当前项目）：

- `<topic>-presentation.pptx`
- `<topic>-speaker-notes.md`
- `<topic>-preview.png` 或 contact sheet
- `<topic>-qa-manifest.json`
- `<topic>-style-adherence-report.json`
- `<topic>-delivery-report.json`
- `<topic>-change-summary.md`（改进已有 deck 时）
- 按需的 PDF、提词版、质量报告和 revision manifest

最终回复必须报告每项文件的绝对路径与存在性、页数、静态风险摘要、渲染 QA 状态，以及状态是 `complete`、`incomplete` 还是 `blocked`。
