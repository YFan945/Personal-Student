# 安全策略

## 报告漏洞

如果您发现安全漏洞，**请勿公开披露**。请通过以下方式报告：

- 发送邮件至项目维护者
- 在 GitHub 上创建 Private Advisory

我们会在 48 小时内确认收悉，并尽快修复。

## 安全边界

本插件的安全模型基于：

1. **工作流状态机** — 通过 `workflow_guard.py` 显式状态命令（init/confirm/transition）记录 PPTX 生产状态，由 SKILL 文本自律维护
2. **Production Summary 确认** — 用户必须明确确认 Production Summary 后才开始生产
3. **QA manifest** — 交付必须附带可验证的质量证据
4. **路径安全** — 环境变量 `CLAUDE_PROJECT_DIR` 有路径穿越防护
