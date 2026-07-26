# PPTX 独立运行时适配与验收计划

## 1. 目标与不可变边界

本计划面向 `student-presentation-suite` 的 Claude Code PPTX 生产能力。目标是让插件
完全拥有创建、OOXML 编辑、渲染和交付检查逻辑，不再运行时依赖外部
`document-skills`、其安装状态或本地缓存路径。

不可变边界：

- 不恢复外部 `document-skills` 依赖；
- 不重新复制已删除的上游 `pptx_skill` 目录；
- 不把 Codex runtime、生成的 PPTX/PNG、cache 或 `node_modules` 放入发布包；
- 已有 deck 的编辑必须保留原件，输出到新文件；
- `intake_pending` 期间不得运行生成、渲染、环境检查或交付命令；
- 用户产物只能写入项目 `outputs/`，不能写进插件安装目录。

历史缓存
`C:\Users\28603\.claude\plugins\cache\anthropic-agent-skills\document-skills\fa0fa64bdc96\skills\pptx`
仅作为来源审计证据，不是运行时入口。许可证与所有权记录见
`plugins/student-presentation-suite/references/pptx-runtime-provenance.md`。

## 2. 当前架构

稳定入口：

- `scripts/pptx_tool.py`：suite-owned CLI facade；
- `scripts/run_with_pptxgenjs.js`：固定解析 PptxGenJS，并执行安全生成协议；
- `shared/pptx_runtime/`：package、edit、chart、schema、render、thumbnail 实现；
- `skills/student-presentation-ppt/references/`：按任务选择性加载的生产说明；
- `tests/test_pptx_tool.py` 与 `tests/test_pptx_runtime.py`：运行时契约。

工作流：

1. `intake_pending`：只检查用户材料并补齐需求；
2. `intake_confirmed`：用户确认完整 Production Summary；
3. `planned`：生成并验证 Presentation Brief、Slide Spec；
4. `producing`：选择 `create`、`edit_ooxml` 或 `rebuild_from_source`；
5. `qa`：package/schema、静态、渲染和逐页视觉检查；
6. `complete`：哈希绑定最终 PPTX、预览和 QA manifest。

## 3. 已实现能力

### 3.1 生成与非覆盖边界

- PptxGenJS 必须使用显式 `--output <new.pptx>`；
- wrapper 拒绝已存在输出、脚本文件和已有输入路径；
- deck 先写同目录随机临时文件；
- `normalize-generated` 只能从 source 写到不同且不存在的 output；
- 归一化成功后才原子重命名为最终输出；
- 任一步失败都会清理临时文件，不会改写模板或已有 deck。

### 3.2 OPC package 与编辑

- 拒绝绝对路径、`..`、symlink 和逃逸目标；
- 限制 package 成员数、单成员大小、总解压大小和压缩比；
- pack 使用流式复制和临时输出；
- 支持新增、复制、删除和完整重排 slide；
- 注册 slide ID、relationship 和 content type；
- 复制 slide 时选择性深复制 notes/comments、chart、SmartArt、embedded package、
  OLE 等可变依赖；
- notes 的反向 slide relationship 会重定向；
- clean 使用临时 trash 与 rollback，保护 package roots 和已注册 slide。

### 3.3 校验

- XML 可解析性、part root、relationship source/target/id；
- content type default/override、slide ID 与 presentation 注册；
- notes slide/master 引用；
- classic chart axis、series、cache、formula 与 embedded workbook 语义；
- ChartEx 由通用 part-root 检查和 Open XML SDK 覆盖，不声称自有完整语义实现；
- Open XML SDK 3.5.1 执行 markup/schema validation；
- suite-owned 规则补充 OPC 和 presentation 语义；
- schema 返回最多 1000 个错误，并公开 `max_errors`/`truncated`；
- 输出字段为 `schema_validation`，profile 为
  `openxml-sdk-plus-suite-semantic-v4`；
- 不宣称插件内置完整 PML/DML/OPC XSD 文件集。

### 3.4 风险检测

- shared master/theme 被报告为 `info`，不会让有效 deck 校验失败；
- 风险按 theme/master 聚合，不重复制造 warning；
- 不再根据 `presentation.xml` 子元素顺序推断 notes theme 是否安全；
- chart 稀疏 cache 合法；named/dynamic formula 为 `info`；
- formula/cache 与 series 基数差异为 `warning`，结构损坏才是 `error`。

### 3.5 渲染与预览

- LibreOffice 使用隔离的临时用户 profile；
- Poppler 输出 PNG/JPG；
- PDF 与逐页预览均可生成；
- LibreOffice 跳过隐藏页时，runtime 按原始 slide 顺序插入明确占位图；
- thumbnail/contact sheet 支持隐藏页标签、分页网格和逐页 metadata；
- metadata 包含 slide 顺序、ID、part、标题、文本预览、layout、notes、comments、
  chart 数、hidden 状态和页面尺寸；
- QA manifest 绑定最终 PPTX/preview 哈希与完整页码覆盖。

### 3.6 Linux AF_UNIX 兼容

- 仅 Linux 且探测到 AF_UNIX 被阻断时编译 suite-owned shim；
- 正常 Linux、Windows 和 macOS 不加载；
- CI 用 `PPTX_RUNTIME_FORCE_AF_UNIX_SHIM=1` 强制走 denial simulation；
- render matrix 必须从实际 render JSON 中看到
  `AF_UNIX denial simulation active`，否则失败。

### 3.7 安装与供应链

- Python、npm、NuGet 依赖均有固定依赖文件；
- .NET 8 SDK 默认要求用户预装；
- 只有显式 `-InstallDotNetSdk` 才下载固定 8.0.423 到用户目录；
- CI 的 `pip-audit`、`npm audit`、NuGet vulnerability scan 均为阻断门禁；
- release checker 拒绝必需文件只存在于工作区但未被 Git 跟踪；
- release checker 拒绝 Codex-only 路径、生成文件、cache 和大小写冲突。

## 4. 验收矩阵

### 4.1 静态与单元测试

```powershell
$env:PYTHONPATH=(Resolve-Path "plugins/student-presentation-suite").Path
ruff check plugins/student-presentation-suite/shared/ `
  plugins/student-presentation-suite/scripts/ `
  plugins/student-presentation-suite/tests/
npx --prefix plugins/student-presentation-suite eslint `
  plugins/student-presentation-suite/scripts/*.js
npx --prefix plugins/student-presentation-suite prettier --check `
  plugins/student-presentation-suite/scripts/*.js
python -m unittest discover -s plugins/student-presentation-suite/tests
```

必须覆盖：

- wrapper 明确输出、拒绝覆盖、失败清理；
- package traversal、symlink、zip bomb 和 size limits；
- 增删复制重排后 source bytes 不变；
- notes/comments/chart/embedded workbook relationship；
- 真实 PptxGenJS `addChart` 正向样例；
- malformed classic chart 与 Open XML schema 反向样例；
- shared master/theme 为 info；
- 隐藏页 placeholder 的顺序和数量；
- AF_UNIX shim 探测与强制路径。

### 4.2 Runtime 与渲染

```powershell
python plugins/student-presentation-suite/scripts/smoke_pptx.py
python plugins/student-presentation-suite/scripts/scenario_render_matrix.py --require-render
python plugins/student-presentation-suite/scripts/check_claude_pptx_env.py --json --strict
```

渲染验收要求：

- PPTX、PDF、逐页 preview 均存在；
- preview 数量等于 PPTX slide 数，包括隐藏页占位；
- 9 个场景均通过 package、render、manifest 和 strict delivery；
- Linux CI 强制 shim 路径确实被激活，而不是仅设置环境变量。

### 4.3 发布

```powershell
python plugins/student-presentation-suite/scripts/check_plugin_release.py --json
python scripts/check_marketplace_release.py --json
python scripts/check_installed_version.py --source-only --json
claude plugin validate --strict .\plugins\student-presentation-suite
claude plugin validate --strict .
git diff --check
```

发布前还必须确认：

- 当前分支是 `claude-code`；
- 所有 `REQUIRED_FILES` 已被 Git 跟踪；
- 工作区没有 `.pptx`、`.png`、cache、`node_modules`；
- README/README-zh、CHANGELOG 与行为一致；
- 不存在外部缓存路径的运行时引用；
- 远端 Linux render matrix 与安全审计成功。

## 5. 尚需外部环境确认的事项

代码与本地测试不能替代以下发布环境证据：

- 真实 GitHub Ubuntu runner 中 LibreOffice + forced AF_UNIX shim 的完整 render matrix；
- 远端 `pip-audit`、`npm audit`、NuGet audit；
- 新增 runtime 文件被 stage/commit 后的严格 tracked-file release gate；
- 仓库所有者对 `claude-code` 的最终发布、push 和 tag。

这些是发布验收步骤，不是恢复外部 `document-skills` 依赖的理由。
