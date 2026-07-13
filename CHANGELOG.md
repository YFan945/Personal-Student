# Changelog

本文件记录 `claude-code` 分支的 Claude Code marketplace 与
`student-presentation-suite` 插件版本。版本按时间倒序排列；`main` 分支的
Codex 发行记录不在此维护。

## Unreleased

- 严格交付门禁现在会阻断静态 blocker、损坏/空白预览以及缺少或失效的 QA manifest。
- 新增与 PPTX、渲染预览 hash 和全页检查绑定的 QA manifest，并要求其通过后才能转换到 `complete`。
- 修复超长文本预警的 bridge 字段错误，并改用未舍入的溢出比率进行阈值判断。
- `unblock` 现在回到 `intake_pending`，生产 hook 同时验证 Production Summary 文件与 hash。
- 14 套标准视觉风格现有机器可读 design tokens；production brief 会展开 palette、几何、字体与线条约束，并可生成 style-adherence report。
- Slide Spec 现按 scenario 验证必需 story role，静态检查新增可见对象的大面积重叠风险。
- 新增低分辨率/拉伸图片 blocker、connector 线宽 token 检查，以及 LibreOffice/Poppler 驱动的临时场景渲染矩阵；CI 在 Ubuntu 上强制渲染九种代表性场景。
- 静态 QA 继续增加标题区/页脚区、最小 gutter、前景背景对比度、connector 路由，以及图表标题和标签字号门禁。
- 新增显式文本框 padding、叠放对象对齐误差和图片 containment 的结构化检查。
- delivery check 现可写出包含 static/render/style 证据与最终状态的 `delivery-report.json`。
- QA manifest 现必须明确记录 `scenario_contract_passed: true`，交付报告同步输出该结论。
- 文本溢出估算现在考虑段落、显式换行、bullet 缩进与文本框内边距，降低复杂排版漏报。
- `visual-led` Slide Spec 现强制提供内容页视觉结构；timeline、comparison、process 和 chart 各自验证可生成的结构化 details。
- 静态报告新增 deck 级布局模式统计，配合已有颜色和字体统计支持风格重复审查。

## 0.4.0 — 2026-06-21

### 版本概述

本版本将插件从“生成与审查工作流”扩展为可控的学生演示生产系统，并强化
Claude Code 安装版本一致性。新增 Presentation Brief、Slide Spec v2、
Evidence Ledger、分层内容、结构与质量分析、页面锁定、revision manifest、
训练卡、提词版及扩展交付检查。

### 重大功能

- 自动分类课程汇报、答辩、竞赛、社团展示和研究展示，并按受众深度选择表达。
- 支持问题解决、研究、时间线、对比、案例和产品六种叙事结构。
- 固定目录→逐页主张→PPT 文案→演讲版→Slide Spec 的分层生成流程。
- 新增每页字数、图文比、讲稿、金句、引用、导出和版本控制字段。
- 新增 Evidence Ledger、来源可信度和证据引用完整性检查。
- 新增重复页、逻辑倒退、开头/结尾、密度、AI 套话和证据缺口分析。
- 新增局部修改、锁定页面保护、版本差异和 revision manifest。
- 新增逐页五维评分、训练卡、老师/评委追问和 HTML 提词版。
- 扩展静态 PPTX 几何风险检查与可选 PDF/提词版/质量报告交付门禁。

### Claude Code 与发布

- 新增源码与 `claude plugin list/details` 版本一致性检查。
- 新增插件级 `PreToolUse` hook 和持久化工作流状态，确认前确定性阻断生产脚本。
- 安装脚本在完成 update 后强制验证实际加载版本。
- 修复 README 中合法旧安装 ID 迁移说明被测试误判的问题。
- Marketplace、manifest、package 和 lockfile 同步升级到 `0.4.0`。

## 0.3.0 — 2026-06-20

| 字段 | 内容 |
| ---- | ---- |
| 版本 | `0.3.0` |
| 时间范围 | 2026-06-20 |
| Git 范围 | `claude-v0.2.0` → `claude-code` |
| 发布分支 | `claude-code` |
| 主要贡献者 | YFan945 |

### 版本概述

本版本将 PPTX 工作流升级为确定性的“先澄清、再规划、后生成、最后验证”。
完整需求表和 Production Summary 成为生成与编辑的硬门槛，同时压缩 skill
入口、明确三个 skill 的关系，并将确认后的需求完整传入 Slide Spec 与 Claude
PPTX brief。仓库级和插件级文档也完成重写，形成可安装、可维护、可验证、
可发布的闭环。

### 重大功能

- **完整需求表**：新增 `references/presentation-intake.md`，统一主题、课程、
  汇报类型、受众、语言、时长、页数、成员、评分标准、资料来源、模板、图片
  策略、视觉风格和交付物的确认规则。
- **强制确认门禁**：信息不完整时只展示已确认项和缺失项；每个缺失项附推荐值
  与影响。用户说“你决定”只会采用推荐值，仍需确认完整 Production Summary。
- **确定性状态机**：统一
  `intake_pending → intake_confirmed → planned → producing → qa → complete`，
  并明确 `incomplete`、`blocked` 的进入条件。
- **结构化 intake → Slide Spec**：新增 `topic`、`audience`、
  `source_material`、`visual_style` 和 `deliverables` 字段，并由 bridge 写入
  Claude PPTX 生产 brief。
- **review → edit 交接**：继续以 `source_deck`、`edit_intent`、
  `review_findings`、`preserve` 和 `change_summary_required` 传递已有 deck
  改进要求，且始终生成独立改进版。

### 重要调整

- **Skill 职责重构**：大纲、PPTX 生产、审查三个 skill 分别稳定在 38、60、
  50 行，只保留触发、职责、状态、核心步骤和输出契约。
- **规则归属统一**：澄清与状态归 `presentation-intake.md`，路由和质量标准归
  `shared-standards.md`，结构化交接归 Slide Spec，避免重复规则漂移。
- **生产 reference 精简**：移除与 intake 重复的默认值和提问逻辑，禁止绕过
  intake 直接进入生成。
- **完整文档体系**：重写根级和插件级中英文 README，扩充 `AGENTS.md`，
  增加架构、安装、工作流、验证、版本同步和发布约束。
- **受保护分支发布**：release check 在 PR 中校验目标分支为 `claude-code`，
  直接发布时仍校验当前分支；发布流程统一通过 required checks 和 PR。
- **版本同步**：Marketplace、插件 manifest、`package.json` 和 lockfile
  统一升级到 `0.3.0`。

### 验证记录

- `python -m unittest discover -s plugins/student-presentation-suite/tests`
  — 34 项测试通过。
- `python plugins/student-presentation-suite/scripts/smoke_pptx.py` — 通过。
- 插件 release check 与 marketplace release check — 通过。
- Claude PPTX environment strict check — 通过。
- 插件包与 marketplace 两级 `claude plugin validate --strict` — 通过。
- `git diff --check` — 通过。

### 兼容性与边界

- 仍只支持明确的学生/大学/课程/答辩场景。
- 仍依赖 `document-skills@anthropic-agent-skills` 完成底层 PPTX 生产。
- 不包含 `.codex-plugin`、`agents/openai.yaml`、`artifact-tool` 或 Codex
  runtime 依赖。
- Claude Code 改动只发布到 `claude-code`，不发布到 `main`。

## 0.2.0 — 2026-06-19

| 字段 | 内容 |
| ---- | ---- |
| 版本 | `0.2.0` |
| 时间范围 | 2026-06-13 ~ 2026-06-19 |
| Git 范围 | `2f96064` → `5f9d5d7` |
| Tag | `claude-v0.2.0` |
| 主要贡献者 | YFan945 |

### 版本概述

本版本完成 Claude Code 专用分支、marketplace、安装迁移脚本和运行时闭环，
并系统强化 skill 路由、已有 deck 改进、视觉风格控制、Slide Spec、CI 与
发布检查。

### 重大功能

- 建立 `claude-code` 专用 marketplace，统一安装 ID 为
  `student-presentation-suite@claude-personal`。
- 新增安装与迁移脚本，自动处理旧 `personal` 注册、依赖安装、marketplace
  注册、`document-skills` 安装和插件启用。
- 打通已有 deck 的 review → edit 结构化交接，要求独立改进版和 change
  summary，不覆盖源文件。
- 将视觉风格拆分为菜单与 14 个独立、按需加载的生成控制规范。
- 新增跨 cwd 的 runtime resolver、`pptxgenjs` wrapper、smoke PPTX 与严格
  环境检查。

### Bug 修复

- 修复 CI 测试导入路径和调用目录依赖。
- 修复根目录、插件目录和 Claude cache 之间的资源定位问题。
- 修复 marketplace 名称、manifest 元数据和插件安装 ID 不一致。
- 修复 review 结论无法稳定进入 PPTX 生成 brief 的问题。
- 修复只凭静态 XML 风险就宣称渲染溢出的不可靠判断。

### 重要调整

- 将 Codex manifests、OpenAI agent 文件和 Codex runtime 依赖从 Claude
  package 中移除。
- 用户交付物统一写入当前 Claude 项目的 `outputs/`。
- 收紧学生场景与 PPT 意图门槛，减少对通用 presentation 请求的误触发。
- 强化中英文课堂可读性、anti-AI wording、小组分工和讲稿规范。
- CI 在 Windows/Linux 上运行 schema、测试、smoke 和 release checks，并
  单独执行 Claude strict validation。

### 验证记录

- 单元测试、schema validation、PPTX smoke、release checks 和 Claude strict
  validation 均纳入发布流程。
- Tag：`claude-v0.2.0`。

## 0.1.0 — 2026-06-07

| 字段 | 内容 |
| ---- | ---- |
| 版本 | `0.1.0` |
| 时间范围 | 2026-06-07 |
| Git 范围 | `7a310a5` → `a55b94b` |
| 主要贡献者 | YFan945 |

### 版本概述

首次公开发布学生演示插件与 marketplace 基础结构，提供学生 PPT 大纲、
PPTX 生成和审查三个核心入口，并修正 GitHub clone URL。

### 主要能力

- 初始 student presentation planning、PPTX production 和 review skills。
- 共享课堂可读性、内容密度、语言与 anti-AI writing 规则。
- 基础 Slide Spec、图片策略、示例和发布文档。
- GitHub marketplace clone 与安装入口。
