# Student Presentation Suite for Claude Code

中文 | [English](README.md)

`student-presentation-suite` 是面向大学生课程汇报、答辩和小组展示的 Claude
Code 插件。它将内容规划、可编辑 PPTX 生成和已有 deck 审查拆成独立 skill，
并共享统一的需求表、Slide Spec 与质量标准。

安装 ID：`student-presentation-suite@claude-personal`。

## 三个 Skill

### `sp-outline`

用于 PPT 大纲、叙事主线、逐页口播规划、小组分工、转场、Q&A 准备和可选
Slide Spec。该 skill 不创建也不会声称创建 PPTX。

### `sp-deck`

用于新建可编辑 PPTX，或为已有 deck 生成独立改进版。底层包编辑、校验和渲染
统一通过本套件维护的 `scripts/pptx_tool.py` 与 `shared/pptx_runtime/` 完成；
不加载外部 `document-skills`，也不分发其复制代码。
它会深复制页面的可变依赖，执行 Open XML SDK markup/schema validation 与本套件
package/presentation 语义检查，并生成支持隐藏页和分页的 contact sheet。
clean 具备事务回滚，inspect 返回版本化逐页 metadata；仅当 Linux sandbox 实际阻断
AF_UNIX 时，render 才按需编译并加载内置 shim。

### `sp-review`

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
质量目标默认 `high-score`，引用风格默认课堂引用，两者都不在 intake 中询问。
即使用户说“你决定”，也只是自动采用推荐值，仍需用户通过 `AskUserQuestion`
（确认 / 调整方案 / 更换视觉风格）确认完整 Production Summary。

生产状态为：

`intake_pending → intake_confirmed → planned → producing → qa → complete`

处于 `intake_pending` 时，不得运行环境检查、生成、渲染或交付命令。

插件通过 `workflow_guard.py` 状态机命令（init/confirm/transition）记录状态。
PreToolUse hook 已移除，命令不再自动拦截；状态由 SKILL 文本自律维护——状态未
推进到 `intake_confirmed` 前不运行生产脚本。

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
- `<topic>-presentation-package-report.json`（suite validation 产物，可复用）
- `<topic>-qa-manifest.json`（与 Slide Spec 证据和最终 PPTX 绑定）
- `<topic>-delivery-report.json`（最终门禁证据）
- 已有 deck 改进时的 `<topic>-change-summary.md`
- 按需输出 PDF、HTML 提词版、训练卡、引用清单、质量报告和 revision manifest

用户文件不得写入插件安装目录。

## 视觉系统

PPTX skill 先读取 `skills/sp-deck/references/visual-style-menu.md`，推荐最适合主题的风格，再只加载一个
`visual-styles/` 下的具体风格规范。每个风格都包含颜色角色、字体、几何、
页面配方、图片处理、密度限制和验收检查。

风格是自适应生成方向，不是固定模板。硬约束只保护可读性、证据真实性、来源边界和
内容适配；页面配方、比例、母题和常规密度范围均可根据叙事任务调整。没有合适视觉素材时
允许排版主导页，不能用无意义图标、卡片或引文填空。

深色页使用 `H.paletteMode(tokens, "dark")`，让 canvas、surface、文字和强调色整体切换。
14 种风格还通过可执行 `style_dna` 区分构图、几何、字体处理、图像处理、图表语法、母题及
三档表现强度；风格偏好不能绕过容量、来源或对比度规则。

所有风格共享 `layout-library.json` 中的 36 套可执行页面版式，由 `pptx-layouts.js` 先按内容
可行性过滤，再结合风格、密度和连续轮廓排序。`scripts/visual_system_smoke_gallery.py` 会生成
14×6 风格 gallery 和独立 36 版式 gallery，并在 LibreOffice/Poppler 可用时渲染。

`deck.js` 遵守 `skills/sp-deck/references/pptxgenjs-safety.md` 中的官方 gotchas，并默认使用
`pptx-layouts.js`、`pptx-helpers.js` 与 `pptx-visuals.js`；`pptx-icons.js` 提供约 30 个随 token 着色的矢量图标。`pptx-visuals.js` 用可编辑形状、
连接线、标签和图片/图表结构实现 hero/visual-dominant/process-path/timeline/comparison/
dashboard/architecture/matrix/quote/summary/reference 等布局族。图片默认等比包含并写入 alt text，
图表使用投影可读字号。

## 质量门禁

PPTX 交付要求：

- 环境兼容性检查；
- 输入 Slide Spec 时执行 schema、语义验证；
- 生成可编辑 PPTX（裸 pptxgenjs，遵循官方 gotchas）；
- 提供讲稿；
- 编辑/模板继承路径执行文本提取检查；
- QA manifest 绑定原始 Slide Spec 的 hash，并保证
  Slide Spec/PPTX/package-report hash 一致（spec 自规划期未被改动时不再重复校验）；
- package report 使用完整 suite validation profile，且 Open XML schema 校验已执行并通过；
- 按需生成的 quality report 与原始 Slide Spec 或当前 PPTX hash 一致；
- 使用标准视觉风格时，提供解析后的 design tokens；
- 严格 delivery check 通过；
- 已有 deck 改进提供独立 change summary。

`complete` 还额外要求执行 `workflow_guard.py transition --to complete --pptx <pptx> --qa-manifest <manifest> --delivery-report <report>`。PptxGenJS wrapper 在原子落盘前只做 `normalize-generated`，不做静态门禁；逐页渲染视觉检查为默认单次快循环（渲染全部 → 目检 → 只修有问题的页 → 只重渲染变更页）。QA 发现 blocker 时通过返工边 `transition --to producing --reason <摘要>` 重建，无需 reset 全流程重跑。QA 和 delivery 复用生成阶段的 package report，不重复校验未修改的 deck。CI 也会为 coursework、英语课堂汇报、答辩、竞赛、社团展示、研究展示、软件项目、数据调研和学校模板编辑等场景创建并渲染临时矩阵；不会把生成 deck 或预览提交到仓库。

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
python scripts/check_claude_pptx_env.py --mode edit_ooxml --json --strict
python scripts/pptx_tool.py --help
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
