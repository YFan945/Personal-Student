# Student Presentation Suite for Claude Code

中文 | [English](README.md)

> 本分支是专门适配 **Claude Code** 的插件版本，安装、依赖和运行方式均以
> Claude Code 为准。若你使用 **OpenAI Codex**，请查看
> [`main` 分支](https://github.com/YFan945/student-presentation-suite/tree/main)，
> 不要在 Codex 中安装本分支。

`student-presentation-suite` 用于大学课程汇报、论文答辩、小组展示等学生学术
场景。它可以在 Claude Code 中生成 PPT 大纲和讲稿、创建可编辑 PPTX、审查
已有 PPT，并根据审查结果生成独立改进版。

插件安装 ID：

```text
student-presentation-suite@claude-personal
```

当前 PPT 生成质量保障能力、已知缺口和整改验收标准详见
[PPT-GENERATION-QUALITY-AUDIT.md](PPT-GENERATION-QUALITY-AUDIT.md)。

## 功能

| 需求 | 使用的 Skill | 结果 |
| --- | --- | --- |
| 写 PPT 大纲、逐页内容、讲稿或小组分工 | `student-presentation` | Markdown 规划文档，不创建 PPTX |
| 创建、重做或修改可编辑 PPT/PPTX | `student-presentation-ppt` | PPTX、讲稿和预览图 |
| 审查、评分或诊断已有 PPT | `student-presentation-review` | 默认只读的审查报告 |

PPTX 创建和编辑依赖
`document-skills@anthropic-agent-skills`。安装脚本会一并安装该依赖。

## 结构化工作流与控制

0.4 版本在 Slide Spec/PPTX 工作前增加统一的 Presentation Brief：

- 自动识别课程汇报、答辩、竞赛、社团展示和研究展示；
- 建模受众类型与表达深度；
- 支持问题解决、研究、时间线、对比、案例和产品六种结构；
- 支持新手/熟手交互模式与基础版/高分版质量模式；
- 可控制每页字数、图文比例、讲稿、金句、引用、导出格式和版本管理；
- 按目录→逐页主张→PPT 文案→演讲版→Slide Spec 分层生成；
- 提供 Evidence Ledger、确定性质量报告、页面锁定、revision manifest、训练卡和演练支持。

本地可导出 PPTX、PDF、预览图、Markdown 讲稿、HTML 提词版、质量报告、
引用清单和版本清单。网页编辑与云同步需要外部服务，本插件不虚假声明这些能力。

## 环境要求

安装前请确保已安装：

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Git
- Python 3.10+
- Node.js 与 npm
- LibreOffice 和 Poppler（推荐，用于渲染检查与 PDF 导出；缺失不影响 PPTX 生成）

可先检查基础命令：

```powershell
claude --version
git --version
python --version
node --version
npm --version
```

## 下载与安装

### Windows 推荐方式

在 PowerShell 中执行：

```powershell
git clone --branch claude-code --single-branch `
  https://github.com/YFan945/student-presentation-suite.git `
  "$env:USERPROFILE\.agents\claude-plugins"

Set-Location "$env:USERPROFILE\.agents\claude-plugins"
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_claude_plugin.ps1 -Migrate
```

`-Migrate` 会清理旧的 `student-presentation-suite@personal` 注册和缓存，然后：

1. 安装 Python 与 Node.js 依赖；
2. 注册本地 marketplace `claude-personal`；
3. 安装 `document-skills@anthropic-agent-skills`；
4. 安装并启用 `student-presentation-suite@claude-personal`；
5. 执行严格环境检查并显示插件状态。

安装完成后重启 Claude Code。

### 已经下载过仓库

```powershell
Set-Location "$env:USERPROFILE\.agents\claude-plugins"
git switch claude-code
git pull --ff-only origin claude-code
.\scripts\install_claude_plugin.ps1
```

如果只需重新注册插件、不想重复安装依赖：

```powershell
.\scripts\install_claude_plugin.ps1 -SkipDependencies -SkipMarketplaceClone
```

## 验证安装

```powershell
claude plugin marketplace list
claude plugin list
claude plugin details student-presentation-suite@claude-personal
python .\plugins\student-presentation-suite\scripts\check_claude_pptx_env.py --json --strict
```

应能看到：

- marketplace：`claude-personal`
- 插件：`student-presentation-suite@claude-personal`
- 上游依赖：`document-skills@anthropic-agent-skills`

若刚安装或更新后 Claude Code 没有识别插件，请先完全退出并重新启动 Claude
Code。

## 使用方式

进入你的课程项目目录后启动 Claude Code：

```powershell
Set-Location D:\my-course-project
claude
```

直接用自然语言描述任务即可。插件只处理明确的学生学术展示场景；普通商务
演示、宣传 deck 或非学生任务不会自动进入这些 skill。

创建或修改 PPTX 前，Claude 会整理完整的 `Production Summary`，包括主题、
课程、受众、语言、时长、页数、评分要求、资料来源、视觉风格和交付物。你确认
后才会开始生成。这样可避免在关键信息不完整时直接产出错误文件。

插件通过 `PreToolUse` hook 对生产命令执行确定性门禁，并在项目输出目录保存
已确认摘要的哈希和工作流状态，因此不再只依赖模型是否遵循文字说明。

生成结果默认写入当前项目的 `outputs/` 目录，不会写进插件安装目录。修改已有
PPT 时也不会覆盖原文件。

## 使用案例

### 1. 只生成大纲和讲稿

```text
我是软件工程专业学生，要做一次 6 分钟的中文课程汇报。
主题是“AI 辅助软件测试”，请设计 8 页 PPT 大纲，并给出每页讲稿和时间分配。
不要生成 PPTX。
```

适合先确定内容结构，输出通常包括大纲、逐页讲稿、转场和可选 Q&A。

### 2. 创建可编辑 PPTX

```text
为我的大学课程创建一个可编辑 PPTX。
主题是“生成式 AI 学习反思”，中文，个人汇报，5 分钟，8 页。
受众是老师和同学，风格简洁现代，需要 PPTX、逐页讲稿和预览图。
```

Claude 会补问缺失要求，展示完整 `Production Summary`；确认后再生成和
检查 PPTX。

### 3. 小组课程展示

```text
我们 4 人要做 12 分钟的数据库课程展示，主题是“分布式数据库的一致性”。
请创建 12 页英文 PPTX，安排每位成员负责的页面和讲述时间，附 speaker notes
和可能的老师提问。
```

插件会处理成员分工、交接语句、时间预算和 Q&A 准备。

### 4. 论文答辩 PPT

```text
根据当前项目中的论文、实验结果和图片，为我的本科毕业答辩制作 15 页中文
PPTX，控制在 10 分钟。重点突出研究问题、方法、实验结果、贡献和局限。
引用必须来自我提供的材料，不要编造数据。
```

建议先把论文、数据、图片和学校模板放入当前项目，再启动 Claude Code。

### 5. 只审查现有 PPT

```text
请审查 outputs\defense.pptx，检查内容结构、文字密度、字体大小、图表可读性、
时间分配和答辩风险。只输出问题和具体修改建议，不要改动原文件。
```

该请求默认只读。报告会按严重程度列出目标页面、问题、影响和修改方法。

### 6. 审查并生成改进版

```text
检查 outputs\course-report.pptx，然后直接生成一个改进版。
保留学校模板、logo、已有数据和引用，优化叙事、排版和讲稿，不要覆盖原文件，
并提供修改摘要。
```

插件会先诊断，再要求确认编辑目标，最终生成独立 PPTX 和 change summary。

## 输出文件

根据任务不同，`outputs/` 中可能包含：

```text
<topic>-outline.md
<topic>-presentation.pptx
<topic>-speaker-notes.md
<topic>-preview.png
<topic>-qa-manifest.json
<topic>-style-adherence-report.json
<topic>-delivery-report.json
<topic>-change-summary.md
<topic>-presentation.pdf
<topic>-teleprompter.html
<topic>-training-cards.md
<topic>-quality-report.json
<topic>-revision-manifest.json
```

最终回复会说明文件绝对路径、页数、渲染检查结果，以及任务状态：
`complete`、`incomplete` 或 `blocked`。进入 `complete` 必须提供与当前 PPTX 和
渲染预览 hash 绑定的 QA manifest，其中记录全页检查和零遗留 blocker。
标准视觉风格还会解析为 palette、间距、字体和线条 token，并可生成风格一致性报告。
发布工作流还会在 Linux 上临时渲染课程汇报、英语课堂、答辩、竞赛、社团展示、研究展示、软件项目、数据调查和学校模板编辑场景矩阵。

## 更新与卸载

更新仓库和插件：

```powershell
Set-Location "$env:USERPROFILE\.agents\claude-plugins"
git pull --ff-only origin claude-code
claude plugin update -s user student-presentation-suite@claude-personal
```

卸载插件：

```powershell
claude plugin uninstall student-presentation-suite@claude-personal
claude plugin marketplace remove claude-personal
```

## 常见问题

### 插件没有触发

确认请求同时包含“学生/课程/答辩”等学术场景和明确的 PPT 意图。也可以在请求
中直接写明希望使用 `student-presentation`、`student-presentation-ppt` 或
`student-presentation-review`。

### 环境检查失败

运行：

```powershell
python .\plugins\student-presentation-suite\scripts\check_claude_pptx_env.py --json --strict
python .\scripts\check_installed_version.py --json
```

根据输出安装缺失的 Python、Node.js 或 `document-skills` 依赖。LibreOffice 和
Poppler 缺失时仅影响渲染检查和 PDF 导出，不阻断 PPTX 生成。

### 工作流状态卡住

如果插件提示需要确认 Production Summary 但你想重新开始：

```powershell
python .\plugins\student-presentation-suite\scripts\workflow_guard.py reset
```

如果状态为 `blocked`（环境依赖缺失导致阻断），解决依赖后恢复：

```powershell
python .\plugins\student-presentation-suite\scripts\workflow_guard.py unblock
```

`unblock` 会回到 `intake_pending`；恢复生产前必须重新确认 Production Summary。

### 生成文件在哪里

默认在启动 Claude Code 时所在项目的 `outputs/`。如果设置了
`CLAUDE_PROJECT_DIR`，则位于 `${CLAUDE_PROJECT_DIR}/outputs`。

### Codex 能否使用本分支

不能。本分支只适配 Claude Code。Codex 版本请使用
[`main` 分支](https://github.com/YFan945/student-presentation-suite/tree/main)。

## 开发与发布

本分支的源码、验证和发布约束见 [AGENTS.md](AGENTS.md) 和
[CHANGELOG.md](CHANGELOG.md)。Claude Code 版本只发布到 `claude-code`，
不得发布到 `main`。

## License

MIT，见 [LICENSE](LICENSE)。
