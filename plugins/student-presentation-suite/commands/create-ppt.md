---
name: create-ppt
description: 创建学生演示文稿 PPT/PPTX。提供主题后引导完成 intake、规划、生成和质检全流程。
---

# 创建学生演示文稿

加载 `skills/student-presentation-ppt/SKILL.md` 的工作流。严格按
intake → 规划 → 生产 → QA → 完成的顺序推进。使用 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py`
管理状态门禁。

## 快速参数

用户可以提供：
- 主题（必填）
- 时长、受众、语言等 intake 参数（可选，缺失时逐个交互确认）
- 已有源文件路径（编辑模式）
