# PPTX QA And Completion

QA 必须绑定最终 candidate，顺序如下。

## 1. Content

生成后**所有模式（含 create）都做一次内容 QA**，核对缺页、顺序、错字与残留占位符
（对齐 document-skills pptx skill 的 Content QA；`pptx_tool.py inspect --text-output`
内部即 markitdown）：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" inspect <candidate.pptx> \
  --text-output <work-dir>/<topic>-text.md
```

- create 模式以已验证 Slide Spec + deck.js 为内容基线，用上面的文本提取核对每页文字
  与 spec 一致、无错字、顺序正确。
- 模板继承 / `edit_ooxml` / 外部工具改写等场景，除文本提取外追加占位符扫描：
  `markitdown <pptx> | grep -iE "\bx{3,}\b|lorem|ipsum|\bTODO|\[insert|this.*(page|slide).*layout"`
  命中占位符则修 generator 后重建，不手改打包 XML。
- 编辑任务同时核对 preserve/change summary。

## 2. Package evidence

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" validate <pptx> \
  --output <package-report.json> --json
```

优先复用 producing 阶段生成且 PPTX SHA-256 一致的 package report；只有文件发生变化、
报告缺失或 hash 过期才重新执行命令。模板或 source-derived 文件增加
`--original <source>`。校验覆盖 XML 可解析性、part root、
relationship source/target/ID、content type、slide 注册、notes 反向关系、master/theme
共享风险、chart axis、series/cache/formula、externalData/embedded workbook 语义，并通过 Open XML SDK 校验完整 package
中的 PML/DML/OPC markup；相关错误均为 blocker，不能由 LibreOffice 能渲染来豁免。
孤立 content-type override 作为 warning 报告。报告必须保留 `validation_profile` 和
`schema_validation` 字段；必须是 `openxml-sdk-plus-suite-semantic-v4` 且
`schema_validation.performed=true`，否则 package QA 不完整。这里表示
Open XML SDK markup/schema validation 加 suite-owned OPC 语义检查，不宣称内置
完整 PML/DML/OPC XSD 文件集。

## 3. Render and visual inspection（默认必做）

package validation（第 2 节）是强制结构门禁；逐页渲染+视觉目检**默认必做**，用于发现
文字溢出、重叠、边距、对比度等视觉质量问题。做**单次快循环**，不做多轮折腾（对齐
document-skills pptx skill 的 "re-render only the slides you changed, and stop"）：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" render <pptx> \
  --output-dir <work-render-dir> --prefix <topic>
```

1. 渲染全部页面。
2. 逐页检查 overflow、clipping、重叠、边距、对比度、对齐、图片比例/分辨率、chart
   标签、引用和残留 placeholder。
3. 首个 candidate 全部通过时结束视觉检查，不制造修复轮次。
4. 只有发现问题才修改 generator，并**只重渲染变更页**，不要整包重建。

仅当用户明确要求跳过渲染时才豁免（`--allow-missing-preview`）。未渲染时 QA manifest 不写
preview/visual_inspection 字段，delivery 的 `preview_page_coverage` 为 `0/0`；用户明确
放弃视觉 QA 时代码允许 complete（见第 6 节），无需走恢复边补渲染。用户明确不需要讲稿时
同理用 `--allow-missing-notes`。

## 4. QA manifest

调用 `pptx_tool.py qa-manifest`。必须传入原始 `--slide-spec`、
`validate_slide_spec.py --output` 产生的 Slide Spec report，以及可选的
`--package-report <validate --output 产物>`。manifest 验证 Slide Spec/Spec report 的
SHA-256、PPTX 页数后自行写入 `scenario_contract_passed=true`；命令行不允许自报该布尔值。
**spec 自规划期未被改动时不再重复校验**（规划期已由 validate_slide_spec.py 校验），QA
只做 hash 绑定与页数核对；spec 被改动时才重校验以捕获漂移。
`--preview` 与 `repair_cycles` 均为**可选**：只有实际渲染并逐页检查时才传 preview，
manifest 才记录 preview/visual_inspection 字段；`repair_cycles` 是记录字段（0=无返工），
不设下限。`visual_inspection.completed` 由"提供 preview 且 `--remaining-blockers 0`"推导；
`--no-repair-needed-reason` 为可选说明，不再强制。manifest 自动写入最终 PPTX、
package report（若提供）和每个 preview 的 SHA-256，不得手写或复制旧 hash。
strict delivery check 复用 manifest 绑定的 package report。

## 5. Suite checks

运行 `pptx_delivery_check.py --strict --json`。delivery command 显式传入 PPTX、notes、
可选的 preview、package report、已经存在的 QA manifest、输出 report，
以及已确认的 PDF/teleprompter/revision manifest。禁止在 QA manifest 尚未生成时运行
strict delivery。package report 必须使用 `openxml-sdk-plus-suite-semantic-v4` profile，
且 `schema_validation.performed=true`、`error_count=0`；quality report
（`analyze_presentation_spec.py` 的规划期产物，针对 Slide Spec 内容质量）会校验
Slide Spec SHA-256，过期或手写报告不能通过；它不绑定最终 PPTX。preview 文件本身有效
但 hash 与 manifest 不一致（预览在 manifest 之后重新渲染）时，delivery 判为 **warning**
而非 error，不阻断交付；报告中可见该警告，建议重建 manifest 或接受现状。未渲染时以
`--allow-missing-preview` 运行 delivery（见第 3 节）。

## 6. Completion

package validation 通过、所有确认的 deliverables 存在且 delivery check 通过时，状态才能
进入 `complete`。最后的 `transition --to complete` 必须同时传入当前 PPTX、QA manifest
和严格 delivery report；package report 可选（完成门禁信任 delivery report）。
未渲染（`preview_page_coverage=0/0` 且无 visual_inspection）时，只要用户明确放弃视觉 QA，
代码允许 complete（与 `workflow_guard.py` 行为一致）；不再强制走 `incomplete → qa`
恢复边补渲染。

QA 发现问题时**无需重置**：先 `transition --to producing --reason <blocker 摘要>` 返工，
修改 generator 重建后 `transition --to qa`，再重新 qa-manifest 与 delivery check。
只有确认无从修复时才使用 `reset` 回到 intake_pending 重新规划。
