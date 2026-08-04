# PPTX QA And Completion

QA 必须绑定最终 candidate，顺序如下。

## 1. Content

新建 deck 直接以已验证 Slide Spec 和 deck.js 为内容证据，不重复提取同一份文字。
只有 `edit_ooxml`、模板继承、外部工具改写或页数/内容可疑时，才用
`pptx_tool.py inspect --text-output` 检查缺页、顺序、错字、placeholder 和引用。
编辑任务同时核对 preserve/change summary。

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

## 3. Render and visual inspection（可选）

package validation（第 2 节）是唯一强制结构门禁；逐页渲染视觉检查**可选**，用于发现
文字溢出、重叠、边距、对比度等视觉质量问题。仅在 package validate 通过后怀疑布局问题
（或用户要求）时才运行渲染：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" render <pptx> \
  --output-dir <work-render-dir> --prefix <topic>
```

逐页检查 overflow、clipping、重叠、边距、对比度、对齐、图片比例/分辨率、chart 标签、
引用和残留 placeholder。首个 candidate 全部通过时结束视觉检查，不制造修复轮次。
只有发现问题时才修改 generator 并整包重建；修改后重新执行 package、render 和全部页面
检查，不能复用旧 PDF 或 preview。

未做渲染时，QA manifest 不写 preview/visual_inspection 字段，delivery 的
`preview_page_coverage` 为 `0/0`；渲染预览仅供按需自查，不再作为交付强制项。

## 4. QA manifest

调用 `pptx_tool.py qa-manifest`。必须传入原始 `--slide-spec`、
`validate_slide_spec.py --output` 产生的 Slide Spec report，以及可选的
`--package-report <validate --output 产物>`。manifest 会重新执行 schema/语义校验，并
验证 Slide Spec/Spec report 的 SHA-256、PPTX 页数后自行写入
`scenario_contract_passed=true`；命令行不再允许自报该布尔值。
`--preview` 与 `repair_cycles` 均为**可选**：只有实际渲染并逐页检查时才传 preview，
manifest 才记录 preview/visual_inspection 字段；`repair_cycles` 是记录字段（0=无返工），
不设下限。manifest 自动写入最终 PPTX、package report（若提供）和每个 preview 的
SHA-256，不得手写或复制旧 hash。
strict delivery check 复用 manifest 绑定的 package report。

## 5. Suite checks

运行 `pptx_delivery_check.py --strict --json`。delivery command 显式传入 PPTX、notes、
可选的 preview、package report、已经存在的 QA manifest、输出 report，
以及已确认的 PDF/teleprompter/revision manifest。禁止在 QA manifest 尚未生成时运行
strict delivery。package report 必须使用 `openxml-sdk-plus-suite-semantic-v4` profile，
且 `schema_validation.performed=true`、`error_count=0`；quality report 会校验
Slide Spec/PPTX SHA-256，过期或手写报告不能通过。未渲染时 preview 参数可省略。

## 6. Completion

package validation 通过、所有确认的 deliverables 存在且 delivery check 通过时，状态才能
进入 `complete`。最后的 `transition --to complete` 必须同时传入当前 PPTX、QA manifest
和严格 delivery report；package report 可选（完成门禁信任 delivery report）。

QA 发现问题时**无需重置**：先 `transition --to producing --reason <blocker 摘要>` 返工，
修改 generator 重建后 `transition --to qa`，再重新 qa-manifest 与 delivery check。
只有确认无从修复时才使用 `reset` 回到 intake_pending 重新规划。
