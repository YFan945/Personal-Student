---
name: check-pptx-env
description: 检查 PPTX 生产环境就绪状态。验证 Python、Node.js、LibreOffice、Poppler 等依赖。
---

# 检查 PPTX 生产环境

运行 `${CLAUDE_PLUGIN_ROOT}/scripts/check_claude_pptx_env.py --json` 输出环境诊断。

## 模式

- 默认：`--mode all` — 检查全部模式依赖；**对纯编辑任务过严**（会要求 node/pptxgenjs），编辑任务请改用 `--mode edit_ooxml`
- 生成模式：`--mode create` — 检查生成模式依赖
- 重建模式：`--mode rebuild_from_source` — 复用 create 依赖
- 编辑模式：`--mode edit_ooxml` — 检查 OOXML 编辑和 .NET SDK
- 严格模式：`--strict` — 仅 required 依赖缺失时返回失败（LibreOffice/Poppler/markitdown 为推荐项，缺失不失败；未渲染时以 `--allow-missing-preview` 交付，状态为 incomplete）
