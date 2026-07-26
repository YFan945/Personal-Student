# Existing Deck Editing

编辑已有 deck 默认使用 `edit_ooxml`，source 始终只读。

## Required order

1. `inspect` source，记录 SHA-256、页数和文本；
2. `thumbnail` 并建立 source slide 到 Slide Spec 的映射；
3. `unpack` 到新的 work directory；
4. 先完成 add/delete/reorder 等结构操作；
5. 再修改文字、图片、样式、notes 和 relationships；
6. `clean`；
7. `pack --output <new.pptx>`；
8. `validate <new.pptx> --original <source> --output <new-stem>-package-report.json --json`；
9. 对最终新文件只运行一次 `static-check --output <new-stem>-static-report.json`；
10. 验证 preserve contract，生成 change summary；
11. 再进入共享 visual QA，并复用 static/package reports；未修改新文件时不重复运行。

## Editing constraints

- 不手工复制或删除 slide XML；用 facade 的 `add-slide`、`delete-slide` 和
  `reorder-slides` 维护注册信息。
- 结构命令的 package 模式必须提供不同的 output；不得使用上游默认原位覆盖行为。
- facade 复制 slide 时会深复制 notes、comments、chart、SmartArt data 和 embedded
  package/oleObject，并修复 notes slide 的反向关系；layout、master、theme 和普通图片
  仍按 OOXML 共享。新增 relationship type 必须先加入复制策略和回归测试，不能静默共享。
- XML transform 使用不会改写 namespace prefixes 的方法；替换文本时保留 paragraph/run
  格式和 `xml:space="preserve"`。
- 模板 slot 数与内容不一致时删除完整 group，而不是只清空文字。
- 所有 list item 使用独立 paragraph，bullet 继承 layout 或显式 override。
- `.ppt` 必须先转换为 `.pptx`；`.potx` 是否输出为 template 由确认的 deliverable 决定。
- 任何 rebuild 都要切换为 `rebuild_from_source` 并记录原因。
