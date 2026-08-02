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

## 3. Render and visual inspection

生成 wrapper 不输出 static report（静态门禁已剥离）。渲染后逐页检查文字溢出、重叠、
边距、对比度等视觉质量；正确性以第 2 节 package validation 为准。

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" render <pptx> \
  --output-dir <work-render-dir> --prefix <topic>
```

逐页检查 overflow、clipping、重叠、边距、对比度、对齐、图片比例/分辨率、chart 标签、
引用和残留 placeholder。首个 candidate 全部通过时结束视觉检查，不制造修复轮次。
只有发现问题时才修改 generator 并整包重建；修改后重新执行 package、render 和全部页面
检查，不能复用旧 PDF 或 preview。

LibreOffice 或 Poppler 缺失时允许保留候选 PPTX，但状态只能为 `incomplete`。

## 4. QA manifest

完成逐页检查后调用 `pptx_tool.py qa-manifest`。必须传入原始 `--slide-spec`、
`validate_slide_spec.py --output` 产生的 Slide Spec report，以及可选的
`--package-report <validate --output 产物>`。manifest 会重新执行 schema/语义校验，并
验证 Slide Spec/Spec report 的 SHA-256、PPTX 页数后自行写入
`scenario_contract_passed=true`；命令行不再允许自报该布尔值。
preview 数必须等于 slide 数。首个 candidate 通过时使用 `repair_cycles=0` 并记录具体
`no_repair_needed_reason`；只有实际修改过才增加 repair cycle。manifest 自动写入最终
PPTX、package report（若提供）和每个 preview 的 SHA-256，不得手写或复制旧 hash。
strict delivery check 复用 manifest 绑定的 package report。

## 5. Suite checks

运行 `pptx_delivery_check.py --strict --json`。delivery command 显式传入 PPTX、notes、
所有 preview、package report、已经存在的 QA manifest、style report、输出 report，
以及已确认的 PDF/teleprompter/revision manifest。禁止在 QA manifest 尚未生成时运行
strict delivery。package report 必须使用 `openxml-sdk-plus-suite-semantic-v4` profile，
且 `schema_validation.performed=true`、`error_count=0`；quality/style report 会分别校验
Slide Spec/PPTX SHA-256，过期或手写报告不能通过。

## 6. Completion

只有 package validation 通过、全部页面已检查、remaining blockers 为零、所有确认的
deliverables 存在且 delivery check 通过时，状态才能进入 `complete`。最后的
`transition --to complete` 必须同时传入当前 PPTX、QA manifest、package report 和严格
delivery report；自报的 `remaining_blockers=0` 不能单独完成交付。
