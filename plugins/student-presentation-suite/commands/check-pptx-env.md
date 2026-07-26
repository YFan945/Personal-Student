---
name: check-pptx-env
description: 检查 PPTX 生产环境就绪状态。验证 Python、Node.js、LibreOffice、Poppler 等依赖。
---

# 检查 PPTX 生产环境

运行 `${CLAUDE_PLUGIN_ROOT}/scripts/check_claude_pptx_env.py --json` 输出环境诊断。

## 模式

- 默认：`--mode create` — 检查生成模式依赖
- 编辑模式：`--mode edit_ooxml` — 检查 OOXML 编辑和 .NET SDK
- 严格模式：`--strict` — 任何缺失都返回失败
