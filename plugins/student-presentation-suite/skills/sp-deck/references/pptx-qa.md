# PPTX QA And Completion

默认只使用三道门禁。不要为普通生成任务创建 content QA、asset report、visual-inspection
report 和 QA manifest 等中间证据链；这些细粒度命令仅用于排错、模板高风险编辑或用户明确要求
审计报告的场景。

## Gate 1 — Plan

用一个命令完成 Slide Spec schema、跨字段语义和 Brief 交接检查：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_slide_spec.py" <slide-spec> \
  --brief <brief> --output <slide-spec-report.json> --json
```

`analyze_presentation_spec.py` 默认只提供写作建议，不属于完成门禁。发现来源不可追溯、未知
evidence ref 或结构无效时仍须修改 Slide Spec；普通密度、过渡句和措辞建议不阻断生产。

## Gate 2 — Final PPTX

对最终 candidate 只执行两项机器检查和一次人工动作：

1. `pptx_tool.py validate`：检查 Open XML SDK schema 和 suite package semantics。
2. `pptx_tool.py render`：完整渲染全部页面。
3. 逐页查看预览，确认没有裁切、溢出、重叠、低对比、错误图片比例、残留占位符或明显内容漂移。

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" validate <pptx> \
  --output <package-report.json> --json
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" render <pptx> \
  --output-dir <render-dir> --prefix <topic>
```

模板或 source-derived 输出继续给 `validate` 传 `--original <source>`。candidate 改变后重跑
本门禁；只允许一次完整重建，仍有 blocker 时交付 `incomplete`。

## Gate 3 — Delivery

用一次简化交付检查合并预览有效性、页数覆盖、规划报告、package report、用户要求的输出文件
和最终 PPTX hash：

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sp-deck/scripts/pptx_delivery_check.py" \
  --simple --strict --visual-reviewed \
  --pptx <pptx> --slide-spec-report <slide-spec-report.json> \
  --package-report <package-report.json> \
  --preview <page-1.png> --preview <page-2.png> \
  --notes <speaker-notes.md> --output <delivery-report.json> --json
```

每页必须对应一张有效 PNG/JPEG 预览；缺预览或未传 `--visual-reviewed` 时状态只能是
`incomplete`。用户明确不需要 notes 时可传 `--allow-missing-notes`。

交付报告通过后直接完成状态：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/workflow_guard.py" transition --to complete \
  --pptx <pptx> --delivery-report <delivery-report.json>
```

`complete` 仍要求：Production Summary 未变化、Slide Spec 校验通过、package validation
通过、预览覆盖全部页面、人工视觉检查已确认、交付报告绑定当前 PPTX。

## Advanced evidence mode

旧的 `content-qa`、`validate-asset-manifest`、`visual-inspection`、`qa-manifest` 和 evidence-chain
delivery 接口保持兼容，但不再是默认流程。仅在以下情况使用：

- 用户明确要求逐项审计证据；
- 高风险模板/OOXML 编辑需要保存细粒度诊断；
- 外部素材的许可、alt text 或来源必须单独归档；
- 排查 content drift、preview hash 或 package relationship 问题。
