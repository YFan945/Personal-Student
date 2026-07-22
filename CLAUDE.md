# Student Presentation Suite — Claude Code 插件

## 项目结构

```
claude-plugins/
  .editorconfig                 # 跨编辑器格式基线
  .github/
    dependabot.yml              # 自动依赖更新
    workflows/validate.yml      # CI：测试 + lint + 安全扫描 + 场景渲染
    ISSUE_TEMPLATE/bug_report.md
    PULL_REQUEST_TEMPLATE.md
  CONTRIBUTING.md               # 贡献指南
  SECURITY.md                   # 安全策略
  CLAUDE.md                     # 本文件
  AGENTS.md                     # 仓库级 AI 代理指南
  scripts/                      # 仓库级工具脚本
  plugins/student-presentation-suite/
    shared/                     # 共享 Python 模块
      types.py                  # TypedDict 类型定义（新增）
      presentation_quality.py
      pptx_static_core.py
      runtime_paths.py
      _import_helpers.py
      ...
    scripts/                    # CLI 脚本（Python + Node.js）
      pptx-helpers.js           # pptxgenjs 辅助函数
      workflow_guard.py         # 工作流状态机
      ...
    skills/                     # Claude Code 技能定义
    references/                 # 设计标记、JSON Schema、策略文档
    tests/
      test_helpers.py           # 共享测试工具（新增）
      test_end_to_end.py        # 集成测试（新增）
      ...
    pyproject.toml              # Ruff + mypy 配置（新增）
    .eslintrc.json              # JS 代码质量（新增）
    .prettierrc                 # JS 格式化（新增）
    .env.example                # 环境变量文档（新增）
    examples/                   # 使用示例
```

## 常用命令

```bash
# 运行全部测试
cd plugins/student-presentation-suite
PYTHONPATH=. python -m unittest discover -s tests

# 运行单个测试文件
PYTHONPATH=. python -m unittest tests.test_workflow_guard

# 代码质量
ruff check shared/ scripts/ tests/
npx eslint scripts/*.js
npx prettier --check scripts/*.js

# PPTX 环境检查
node scripts/run_with_pptxgenjs.js --probe
```

## 依赖

- Python: `requirements.txt` + `requirements-claude-pptx.txt`
- Node.js: `package.json`（pptxgenjs）
- 安全扫描：pip-audit、npm audit（CI 中运行）

## 工作流状态机

```
intake_pending → intake_confirmed → planned → producing → qa → complete
     ↓                ↓                   ↓          ↓          ↓
  blocked          blocked              blocked    blocked    blocked
  incomplete       incomplete           incomplete incomplete incomplete
```

## 已知问题跟踪

质量门禁已知不足记录在 `PPT-GENERATION-QUALITY-AUDIT.md`。

## 设计标记

14 种视觉风格定义在 `references/design-tokens.json` 和
`skills/student-presentation-ppt/references/visual-styles/*.md`。

## 测试工具

所有动态加载脚本的测试文件使用 `from test_helpers import load_module`，
传递 `SCRIPT` 路径参数即可：`load_module(SCRIPT)`。`test_helpers.py`
在 `tests/` 目录下。
