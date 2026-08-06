# Embedded PPTX Runtime

所有低层 PPTX 操作只通过 suite-owned facade 调用：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" <subcommand> ...
```

可用命令：

- `inspect <pptx> [--text-output <md>]`：只读 hash、页数和 versioned slide metadata；
  每页包含 index、slide ID/rId、part、hidden、标题/文本预览、layout、notes、comments、
  charts 和页面尺寸；损坏包仍返回基础 inspect 结果并附 metadata warning；
- `thumbnail <pptx> --output-prefix <path> [--cols N] [--rows N]`：按页面 XML 名称输出
  可分页缩略图；隐藏页保留占位和 `hidden` 标记，不会造成后续页面错标；
- `unpack <pptx> --output <empty-dir>`：安全解包；
- `add-slide <dir|pptx> <slideN.xml|slideLayoutN.xml> ...`：维护 package 关系；
- `delete-slide <dir|pptx> <slideN.xml> ...`：删除页面注册并清理 package 模式的孤立 parts；
- `reorder-slides <dir|pptx> <slideN.xml>...`：以完整、无重复的页面清单替换顺序；
- `clean <unpacked-dir>`：先验证 package roots、slide 注册和全部可达关系，再事务式清理
  孤立 parts；悬空关系、symlink 或中途 I/O 失败时回滚，保证不发生半清理；
- `pack <unpacked-dir> --output <new.pptx>`：确定性重打包；
- `validate <pptx> [--original <source>] --json`：Open XML SDK PML/DML/OPC schema 与
  suite-owned package/OOXML 语义验证；共享 theme/master
  和一个 slide master 影响多页的情况作为风险 warning 输出，不把正常共享结构误判为损坏；
- `render <pptx> --output-dir <dir> --prefix <prefix>`：使用独立 LibreOffice profile 渲染
  PDF 与逐页图；Linux AF_UNIX 被 sandbox 阻断时才编译并加载 suite-owned hashed shim，
  正常 Linux、Windows 和 macOS 不加载；
- `qa-manifest ... --slide-spec <spec> --slide-spec-report <report>
  [--package-report <package-report>]`：重新执行原始 Slide Spec 的 schema/语义校验，
  再把生成契约、逐页检查证据和 package validation 报告绑定到最终 PPTX；不接受自报
  scenario contract。`--package-report` 可选用 `validate --output` 产物，校验
  `ok`/hash/profile/schema_validation。

Package 输入的结构命令强制要求不同的 `--output`；facade 拒绝覆盖 source。
旧的 `skills/.../scripts/pptx_skill/` 已被移除，不得恢复或引用。不要修改
`PYTHONPATH`，也不要在用户项目中临时 `pip install` 或 `npm install`。

## Work directory

每个任务使用 `outputs/.pptx-work/<work-id>/`，其中可包含 unpacked package、deck.js、
PDF 和页面图。正式 deliverables 才写入 `outputs/<topic>-*`。文件名和路径必须显式
传给命令，不能依赖 cwd、shell glob、`rm`、`zip` 或 `grep`。
