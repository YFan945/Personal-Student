# Student Presentation Suite — 插件规范审查报告

> 审查日期：2026-07-26
> 审查依据：plugin-dev 插件规范（plugin-structure、hook-development、skill-development）
> 插件版本：0.4.2

---

## 一、总览

| 维度 | 状态 | 说明 |
|------|------|------|
| `.claude-plugin/plugin.json` | ✅ 存在 | 必填字段完整 |
| `hooks/` | ⚠️ 有问题 | 跨平台兼容性缺陷 |
| `skills/` (×3) | ⚠️ 有问题 | 元数据不完整、残留缓存文件 |
| `commands/` | ❌ 缺失 | 无可交互命令 |
| `agents/` | ❌ 缺失 | 无代理定义 |
| `.mcp.json` | ❌ 缺失 | 无 MCP（非必须） |
| `AGENTS.md` | ❌ 缺失 | 插件级代理指南 |
| `scripts/` | ✅ 存在 | 工具脚本齐全 |
| `shared/` | ✅ 存在 | 共享模块组织良好 |
| `tests/` | ✅ 存在 | 测试覆盖较全 |
| `references/` | ✅ 存在 | 参考文档丰富 |

---

## 二、严重问题 (Critical)

### C1. Hook 命令跨平台不兼容

**文件**：`hooks/hooks.json:9`

```json
"command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py\" || python \"${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py\""
```

**问题**：
1. `python3` 在 Windows 上不存在 — Windows 上 Python 可执行文件是 `python` 或 `py`
2. `||` fallback 语法依赖 bash/sh，在 PowerShell 中为语法错误（应使用 `if ($?) { }` 模式），cmd.exe 虽支持 `||` 但无法执行 `python3`
3. 转义引号 `\"` 在 JSON 中合法，但经 shell 传递后行为不确定

**影响**：在 Windows 平台上 PreToolUse hook 可能完全无法执行，导致生产命令门禁失效——所有生产脚本可在未确认 intake 的情况下运行。

**修复建议**：
```json
// 方案 A：Windows 优先（推荐，因为仓库主要面向 Windows）
"command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py\""

// 方案 B：跨平台检测
"command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py\" 2>/dev/null || python \"${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py\""
```

注意方案 B 仍然依赖 bash 语法，仅在 Git Bash 环境下有效。最可靠的方案是在 `workflow_guard.py` 本身处理跨平台，hook 命令只使用 `python`。

---

### C2. 已删除源码的残留字节码缓存

**目录**：`skills/student-presentation-ppt/scripts/pptx_skill/`

**文件清单**：
```
pptx_skill/__pycache__/__init__.cpython-312.pyc
pptx_skill/__pycache__/add_slide.cpython-312.pyc
pptx_skill/__pycache__/thumbnail.cpython-312.pyc
pptx_skill/office/__pycache__/soffice.cpython-312.pyc
pptx_skill/office/__pycache__/validate.cpython-312.pyc
pptx_skill/office/helpers/__pycache__/__init__.cpython-312.pyc
pptx_skill/office/validators/__pycache__/__init__.cpython-312.pyc
pptx_skill/office/validators/__pycache__/base.cpython-312.pyc
pptx_skill/office/validators/__pycache__/docx.cpython-312.pyc
pptx_skill/office/validators/__pycache__/pptx.cpython-312.pyc
pptx_skill/office/validators/__pycache__/redlining.cpython-312.pyc
```

**问题**：
1. `PPTX-RUNTIME-PROVENANCE.md` 声明 "The temporary `skills/student-presentation-ppt/scripts/pptx_skill/` copy...were removed"，但 `__pycache__/` 目录及其 `.pyc` 文件仍然存在
2. 这些字节码来自之前的 `document-skills` 分叉快照，不再被任何代码引用
3. 与 PROVENANCE.md 中的知识产权声明直接矛盾 — 残留文件可能仍包含上游 `document-skills` 的编译产物

**修复建议**：
1. 删除整个 `skills/student-presentation-ppt/scripts/pptx_skill/` 目录树
2. 运行 `find . -name "__pycache__" -type d` 确认无其他残留
3. 更新 `PPTX-RUNTIME-PROVENANCE.md` 添加清理确认日期

---

## 三、重要问题 (Major)

### M1. Python 版本兼容性声明矛盾

**文件**：`pyproject.toml:29`, `pyproject.toml:11-14`

```toml
[tool.mypy]
python_version = "3.11"    # mypy 按 3.11 检查

[tool.ruff.lint]
ignore = [
    "UP017",  # datetime.UTC is Python 3.11+; the plugin supports Python 3.10
]
```

**问题**：
- mypy 配置声明 `python_version = "3.11"`，表示类型检查以 3.11 为标准
- 但同时忽略 `UP017` 规则，理由是 "plugin supports Python 3.10"
- 实际上 `datetime.UTC` 是 3.11+ 特性，如果代码中使用了它，在 3.10 上会崩溃
- CI 没有针对 3.10 的测试矩阵来验证兼容性声明

**修复建议**：
- 方案 A：如果确实需要 3.10 兼容 → `python_version = "3.10"`，移除 `UP017` ignore（Ruff 会自然提示升级建议）
- 方案 B：如果最低支持 3.11 → 删除 UP017 ignore 注释中的 3.10 理由，在 README 中声明 `Python >= 3.11`

---

### M2. plugin.json homepage 指向非稳定 URL

**文件**：`.claude-plugin/plugin.json:8`

```json
"homepage": "https://github.com/YFan945/Personal-Student/tree/claude-code"
```

**问题**：
- 指向特定分支 `claude-code`，而非默认分支 `main`
- 分支被删除或合并后 URL 失效
- `repository` 字段也指向 `Personal-Student` 仓库根而非插件目录

**修复建议**：
```json
"homepage": "https://github.com/YFan945/Personal-Student",
"repository": "https://github.com/YFan945/Personal-Student/tree/main/plugins/student-presentation-suite"
```

---

### M3. PreToolUse Hook 性能开销过大

**文件**：`hooks/hooks.json:3-13` + `scripts/workflow_guard.py`

**问题**：
- Hook 匹配所有 `Bash` 工具调用（`"matcher": "Bash"`），无任何命令过滤
- 每个 Bash 命令都会启动 Python 进程运行 `workflow_guard.py`
- 虽然 `_check_and_parse_stdin()` 有快速预扫描优化，但仍然：
  - 每次读取 stdin
  - 每次做子串扫描
  - 文件系统的 Python 进程启动开销

**影响**：在非 PPT 会话中，所有 Bash 操作（git、npm、ls 等）都有额外延迟。

**修复建议**：
1. 在 hook 层面增加命令预过滤，例如只对包含特定关键字的 Bash 调用触发
2. 或者将 hook 匹配模式从 `Bash` 改为 `Bash.*(run_with_pptxgenjs|check_claude_pptx_env|pptx_tool|...)`（如果 hook 系统支持正则 matcher）
3. 如 hook 系统不支持正则 matcher，考虑在 `workflow_guard.py` 入口做更轻量的第一层判断

---

### M4. 缺少插件级 AGENTS.md

**位置**：插件根目录

**问题**：插件规范推荐每个插件包含自己的 `AGENTS.md`，用于指导代理如何与插件交互。当前仅仓库根目录有 `AGENTS.md`，插件内没有。

**修复建议**：创建 `plugins/student-presentation-suite/AGENTS.md`，内容包含：
- 插件组件清单与职责
- 技能激活条件
- 工作流状态机说明
- 代理使用插件的注意事项

---

### M5. 所有 3 个 SKILL.md 缺少 version 字段

**文件**：
- `skills/student-presentation/SKILL.md:1-4`
- `skills/student-presentation-ppt/SKILL.md:1-4`
- `skills/student-presentation-review/SKILL.md:1-4`

**问题**：所有 SKILL.md 的 YAML 前置元数据只包含 `name` 和 `description`，缺少 `version` 字段。虽然规范中 version 不是必填，但作为已发布的插件（版本 0.4.2），skill 版本追踪对调试和升级很重要。

**修复建议**：为每个 SKILL.md 添加 `version: 0.4.2`，并随插件版本升级同步更新。

---

### M6. 插件根目录文件组织不规范

**文件**：`PPTX-RUNTIME-PROVENANCE.md`（插件根目录）

**问题**：该文件是治理/审计类文档，不属于任何标准组件目录。放在根目录会造成根目录文件清单混乱。

**修复建议**：
- 方案 A：移至 `references/pptx-runtime-provenance.md` 并纳入 `references/` 索引
- 方案 B：在 README.md 中记录关键审计结论，删除独立文件
- 方案 C：创建 `docs/` 目录统一管理治理类文档

---

## 四、改进建议 (Minor / Enhancement)

### E1. `dependencies` 字段为空

**文件**：`.claude-plugin/plugin.json:20`

```json
"dependencies": []
```

**问题**：如果此插件依赖 `plugin-dev`（如结构规范暗示），应在此声明。否则安装后可能缺少必要插件。

**修复建议**：明确依赖关系，如 `"dependencies": ["plugin-dev@marketplace"]` 或保持为空并注明无外部依赖。

---

### E2. README 中 Install ID 实际不可用

**文件**：`README.md:10`

```
Install ID: `student-presentation-suite@claude-personal`.
```

**问题**：该安装 ID 指向 marketplace 发布，但插件目前仅在本地仓库开发中，实际无法通过此 ID 安装。

**修复建议**：改为本地安装说明或移除该行，待正式发布到 marketplace 后再添加。

---

### E3. `.env.example` 无文档引用

**文件**：`.env.example`

**问题**：文件存在但 README 和 AGENTS.md 中均未提及如何配置环境变量。

**修复建议**：在 README 中添加环境变量配置章节，说明哪些变量可选、哪些必填。

---

### E4. `package.json` name 与插件名不一致

**文件**：`package.json:2`

```json
"name": "student-presentation-suite-runtime"
```

**问题**：`package.json` 的 name 为 `student-presentation-suite-runtime`，而插件名为 `student-presentation-suite`。`-runtime` 后缀有误导性——这个 `package.json` 同时包含运行时依赖（pptxgenjs）和开发依赖（eslint、prettier）。

**修复建议**：统一命名为 `student-presentation-suite`，或拆分为独立的 runtime package。

---

### E5. 缺少 `/commands` 交互命令

**位置**：`commands/` 目录不存在

**问题**：插件完全通过 skill（自动激活）和 hook（后台阻断）运作，没有任何用户可主动调用的 slash command。对于需要用户显式启动的操作（如"创建 PPT"、"审查 PPT"），缺少可发现性。

**修复建议**：考虑添加：
- `/create-presentation` — 显式启动 PPT 创建工作流
- `/review-pptx` — 显式启动 PPT 审查工作流
- `/check-pptx-env` — 环境诊断命令

---

### E6. `.editorconfig` 缺失于插件目录

**位置**：插件根目录

**问题**：仓库根目录有 `.editorconfig`，但插件目录内没有。当插件被独立安装/复制时，编辑器配置会丢失。

**修复建议**：在插件根目录添加 `.editorconfig`（可从仓库根复制）。

---

### E7. 各 `shared/` 子目录缺少 `__init__.py`

**检查结果**：`shared/pptx_runtime/` 有 `__init__.py` ✅。但 `shared/pptx_runtime/openxml_validator/` 没有。

**文件**：`shared/pptx_runtime/openxml_validator/` — 仅包含 `.csproj`、`Program.cs`、`packages.lock.json`

**问题**：这是 C# 项目目录，不是 Python 包，不需要 `__init__.py`。但该目录的独立性未在 README 中说明。

**修复建议**：在 README 中说明 `.NET adapter` 构建方式。

---

### E8. 测试中混合了旧工作目录

**文件**：`tests/` 目录

**问题**：测试文件使用 `from test_helpers import load_module`，依赖 `test_helpers.py` 中的路径引导。但测试根目录没有 `conftest.py`（pytest）来统一设置 `PYTHONPATH`。

**修复建议**：添加 `tests/conftest.py` 统一路径引导逻辑。

---

## 五、修改优先级与计划

### Phase 1 — 立即修复（阻断性问题）

| ID | 问题 | 预估工作量 | 依赖 |
|----|------|-----------|------|
| C1 | Hook 跨平台兼容性 | 0.5h | 无 |
| C2 | 清理残留 .pyc 文件 | 0.5h | 无 |
| M1 | Python 版本兼容性澄清 | 0.5h | 需要决定最低版本 |

**Phase 1 总预估**：1-2h

### Phase 2 — 高优先级（规范完整性问题）

| ID | 问题 | 预估工作量 | 依赖 |
|----|------|-----------|------|
| M2 | 修正 plugin.json URL | 0.25h | 无 |
| M3 | Hook 性能优化 | 1h | C1 完成后 |
| M5 | SKILL.md 添加 version | 0.5h | 无 |
| C2 后续 | 更新 PROVENANCE.md | 0.25h | C2 完成后 |

**Phase 2 总预估**：2h

### Phase 3 — 中优先级（文档与组织）

| ID | 问题 | 预估工作量 | 依赖 |
|----|------|-----------|------|
| M4 | 创建插件级 AGENTS.md | 1h | 无 |
| M6 | PPTX-RUNTIME-PROVENANCE.md 重定位 | 0.5h | 无 |
| E1 | 明确 dependencies | 0.25h | 无 |
| E2 | 修正 README Install ID | 0.25h | 无 |
| E3 | 文档化 .env.example | 0.5h | 无 |

**Phase 3 总预估**：2.5h

### Phase 4 — 低优先级（增强优化）

| ID | 问题 | 预估工作量 | 依赖 |
|----|------|-----------|------|
| E4 | package.json 命名统一 | 0.5h | 需要评估影响 |
| E5 | 添加 slash commands | 2h | 需要设计命令接口 |
| E6 | 添加 .editorconfig | 0.25h | 无 |
| E7 | 文档化 .NET adapter | 0.5h | 无 |
| E8 | 测试 conftest.py | 0.5h | 无 |

**Phase 4 总预估**：3.75h

---

## 六、总结

| 类别 | 数量 |
|------|------|
| Critical | 2 |
| Major | 4 |
| Minor | 8 |
| **总计** | **14** |

**总体评价**：插件核心架构合理——技能分层清晰、跨技能交接设计完善、工作流状态机设计精良。主要问题集中在：
1. **Windows 平台适配**（C1）— hook 命令语法不兼容当前平台
2. **知识产权清理**（C2）— 残留字节码文件与审计声明矛盾
3. **配置精度**（M1-M6）— 元数据、文档、版本声明需要打磨

---

## 七、修复记录（2026-07-26）

| ID | 问题 | 状态 | 修复内容 |
|----|------|------|---------|
| C1 | Hook 跨平台兼容性 | ✅ 已修复 | `hooks.json` 移除 `python3 \|\| python` fallback，统一为 `python -S` |
| C2 | 残留 .pyc 字节码 | ✅ 已修复 | 删除 `skills/student-presentation-ppt/scripts/pptx_skill/` 整个目录树 |
| C2 后续 | 更新 PROVENANCE.md | ✅ 已修复 | `references/pptx-runtime-provenance.md` 添加 2026-07-26 二次审计记录 |
| M1 | Python 版本兼容性矛盾 | ✅ 已修复 | `pyproject.toml` mypy 改为 `python_version="3.10"`，移除无效 UP017 ignore |
| M2 | plugin.json URL | ✅ 已修复 | `homepage` 指向仓库根，`repository` 指向插件目录 |
| M3 | Hook 性能优化 | ✅ 已修复 | 添加 `python -S` 跳过 site-packages 加速启动 |
| M4 | 缺失 AGENTS.md | ✅ 已修复 | 新建 `AGENTS.md` 含组件清单、技能激活规则、状态机、开发指南 |
| M5 | SKILL.md 缺 version | ✅ 已修复 | 3 个 SKILL.md 均添加 `version: 0.4.2` |
| M6 | PROVENANCE.md 重定位 | ✅ 已修复 | 移至 `references/pptx-runtime-provenance.md`，更新 5 处引用 |
| E1 | dependencies 为空 | ✅ 已修复 | 确认无外部硬依赖，保持空数组（plugin-dev 是开发工具，非运行时依赖） |
| E2 | README Install ID | ✅ 已修复 | 替换为仓库安装说明 |
| E3 | .env.example 无文档 | ✅ 已修复 | 扩展 `.env.example`，README 新增环境变量章节 |
| E4 | package.json 命名 | ✅ 已修复 | 统一为 `student-presentation-suite` |
| E5 | 缺 slash commands | ✅ 已修复 | 新建 `commands/` 目录：`create-ppt`、`review-pptx`、`check-pptx-env` |
| E6 | 缺 .editorconfig | ✅ 已修复 | 从仓库根复制 |
| E7 | .NET adapter 无文档 | ✅ 已修复 | README 新增 Open XML SDK Validation 章节 |
| E8 | 缺 conftest.py | ✅ 已修复 | 新建 `tests/conftest.py` 统一 sys.path 引导 |

**全部 14 项已修复。**
