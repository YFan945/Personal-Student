# Student Presentation Suite for Claude Code

中文 | [English](README.md)

`student-presentation-suite` 是面向大学生课程汇报、答辩和小组展示的 Claude
Code 插件。它将内容规划、可编辑 PPTX 生成和已有 deck 审查拆成独立 skill，
并共享统一的需求表、Slide Spec 与质量标准。

安装 ID：`student-presentation-suite@claude-personal`。

## 三个 Skill

### `student-presentation`

用于 PPT 大纲、叙事主线、逐页口播规划、小组分工、转场、Q&A 准备和可选
Slide Spec。该 skill 不创建也不会声称创建 PPTX。

### `student-presentation-ppt`

用于新建可编辑 PPTX，或为已有 deck 生成独立改进版。底层生成和编辑由
`document-skills@anthropic-agent-skills` 提供；本插件负责学生场景工作流、
确认后的需求、风格控制、输出契约和 QA 门禁。

### `student-presentation-review`

用于审查、评分、风险诊断、计划与成品对比和逐页修改建议。默认只读。
用户说“直接改好”时，先完成诊断，再把结构化 findings 交给 PPTX skill。

## 完整 PPTX 需求表

正式生成前必须确认：

- 主题；
- 课程/场景与汇报类型；
- 受众与语言；
- 时长与页数；
- 个人/小组形式及成员；
- 评分标准或必需章节；
- 资料来源和证据边界；
- 模板、logo 或品牌限制；
- 图片来源策略；
- 视觉风格；
- 必需交付物。

插件会复用已确认的信息，只询问缺失项，并为每个缺失项提供推荐值和影响。
即使用户说“你决定”，也只是自动采用推荐值，仍需用户确认完整 Production
Summary。

生产状态为：

`intake_pending → intake_confirmed → planned → producing → qa → complete`

处于 `intake_pending` 时，不得运行环境检查、生成、渲染或交付命令。

插件自带 `PreToolUse` hook 和 `workflow_guard.py`。只有已确认 Production
Summary 的哈希将项目状态推进到 `intake_confirmed` 后，生产脚本才允许执行。

## 结构化交接

Slide Spec YAML 将确认后的规划传入 PPTX 生成。`meta` 可记录主题、汇报类型、
受众、语言、时长、页数、分工、课程、评分标准、资料来源、模板、图片策略、
视觉风格、交付物和输出前缀。

已有 deck 改进额外使用：

- `source_deck`
- `edit_intent`
- `review_findings`
- `preserve`
- `change_summary_required`

原始 deck 永远不会被覆盖。

Slide Spec v2 还可以携带场景、受众深度、结构模式、质量控制、分层文案和讲稿、
Evidence Ledger 引用、锁定页面及 revision 元数据；旧版 Slide Spec 仍兼容。

## 输出文件

交付物写入 `${CLAUDE_PROJECT_DIR}/outputs`；环境变量不可用时，回退到当前
项目的 `outputs/`：

- `<topic>-presentation.pptx`
- `<topic>-speaker-notes.md`
- `<topic>-preview.png` 或 contact sheet
- 已有 deck 改进时的 `<topic>-change-summary.md`
- 按需输出 PDF、HTML 提词版、训练卡、引用清单、质量报告和 revision manifest

用户文件不得写入插件安装目录。

## 视觉系统

PPTX skill 先读取 `visual-style-menu.md`，推荐最适合主题的风格，再只加载一个
`visual-styles/` 下的具体风格规范。每个风格都包含颜色角色、字体、几何、
页面配方、图片处理、密度限制和验收检查。

风格是生成方向，不是固定模板。页面布局必须服务于内容功能，装饰不能代替
证据、层级和可读性。

## 质量门禁

PPTX 交付要求：

- 环境兼容性检查；
- 输入 Slide Spec 时执行 schema 和语义验证；
- 生成可编辑 PPTX；
- 提供讲稿；
- 文本提取检查；
- LibreOffice 渲染和 Poppler 页面图片；
- 视觉检查及至少一轮修复再验证；
- 严格 delivery check 通过；
- 已有 deck 改进提供独立 change summary。

最终状态使用 `complete`、`incomplete` 或 `blocked`。静态 XML 风险不能单独
证明渲染后的裁切或可读性问题。

## Runtime

Claude Code 不会自动安装本包的 Python 和 Node runtime 依赖。可以使用仓库
根目录安装脚本，或在本目录手动执行：

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-claude-pptx.txt
npm ci
```

常用检查：

```powershell
python scripts/check_claude_pptx_env.py --json --strict
python scripts/validate_slide_spec.py path\to\spec.yaml --json
python scripts/validate_presentation_brief.py path\to\brief.yaml --json
python scripts/analyze_presentation_spec.py path\to\spec.yaml --strict --json
python scripts/build_support_outputs.py path\to\spec.yaml --output-dir <project>\outputs --json
python scripts/create_revision_manifest.py old.yaml new.yaml --strict
python scripts/manage_versions.py snapshot --output-root <project>\outputs --revision-id r1 --file <deck>
python scripts/slide_spec_to_pptx_brief.py path\to\spec.yaml --output-dir <project>\outputs
python scripts/bump_version.py 0.5.0 --dry-run  # 统一版本升级
node scripts/run_with_pptxgenjs.js --probe
python scripts/smoke_pptx.py
```

## 包边界

这是 Claude Code 专用包，不包含 `.codex-plugin`、`agents/openai.yaml`、
`artifact-tool` 或 Codex runtime 声明。

安装、维护和发布说明见仓库根目录
[README](../../README-zh.md)、[AGENTS.md](../../AGENTS.md) 和
[CHANGELOG.md](../../CHANGELOG.md)。
