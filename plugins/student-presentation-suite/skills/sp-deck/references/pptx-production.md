# PPTX Production

本文件只负责生产阶段编排。Intake、内容、证据、图片和视觉标准由共享 canonical
references 负责；低层命令见 `pptx-runtime.md`。

生产前必须具备：已确认的 Production Summary、验证通过的 Presentation Brief 与
Slide Spec、明确的 output prefix、selected visual style，以及唯一 production mode。

## Mode decision

| Mode | 使用条件 | 生产机制 |
| --- | --- | --- |
| `create` | 没有 source deck，或 source 为 PDF/preview 等非 PPTX（未损坏） | pptxgenjs + suite helper |
| `edit_ooxml` | 要保留模板、布局或已有内容（含"用这个 PPTX 模板做新 deck"）；source 必须是可解包的 `.pptx`/`.potx` | 解包、结构修改、内容修改、clean、pack |
| `rebuild_from_source` | 原文件损坏或重建更安全，且理由已记录 | 读取原文件后新建，不声称原位编辑 |

`source_deck`、`edit_intent`、`review_findings`、`preserve` 和
`change_summary_required` 是 Slide Spec 顶层字段。判定规则（intake 收集 `source_deck`
与 `edit_intent`，模式由 `slide_spec_to_pptx_brief.py` 推导并复核）：

- 存在可解包的 PPTX/POTX 模板 → `edit_ooxml`（即使目标内容全新也要保留模板）；
  不得因为新建更方便而静默改为 rebuild。
- source 为 PDF/preview 等非 PPTX → **不能** `edit_ooxml`（无法解包）；源文件损坏走
  `rebuild_from_source`，否则 `create`。
- `edit_intent: "rebuild-clean-copy"`（review 交接）优先于"默认 edit_ooxml"，走
  `rebuild_from_source` 并记录理由。

## Shared invariants

- 输出和 work directory 必须在项目 `outputs/` 下。
- source deck 只读，生产前后都记录 SHA-256。
- 中文正文不低于 22pt，英文正文不低于 20pt，主要标题不低于 24pt。
- 文本不适配时依次拆页、删减、扩大容器，禁止突破字号下限；溢出靠 QA 逐页视觉检查。
- 坐标必须落在画布内；标题、正文、页脚区与安全边距保持一致。禁止用
  `slideH - 常量` 自算页脚坐标。可用可选 helper 的 `H.safeArea`/`H.gridLayout` 降低
  手算坐标出错率。
- 按 `pptxgenjs-safety.md` 编写 pptxgenjs 脚本，**默认一致使用**
  `pptx-layouts.js`（`getLayout`/`selectLayouts`/`resolveLayout`）、
  `pptx-composer.js`、`pptx-helpers.js`、`pptx-shapes.js`、`pptx-svg-library.js` 与
  `pptx-visuals.js` 划分版面，避免手写每页坐标导致重叠/溢出；详见
  `pptx-visual-engine.md`。确需自定义构图时仍通过 composer preflight，并遵循
  "Visual design" 节的设计原则。每页用 `slide.background` 设置背景（canvas 角色），
  深色页先用 `H.paletteMode(tokens, "dark")` 得到整套页面 token，再把同一份页面
  token 传给背景、标题、页脚和视觉组件；不得只切换 canvas 而继续使用浅色文字角色。
- 使用 resolved design tokens；不得另选本 reference 之外的 palette。
- 所有最终 candidate 都必须通过 `pptx_tool.py validate`。

## Visual design（对齐 document-skills pptx skill）

把"每页手写坐标"作为兜底而非首选。每页都按这些原则设计，从源头减少视觉返工：

- **按角色用色**：canvas/surface 承担阅读底色，primary/secondary text 承担文字，accent
  只承担重点、状态或导航；不要平均使用全部色彩，也不要把高饱和强调色当普通正文色。
- **深/浅对比（sandwich）**：默认封面与结论页用深色背景、内容页用浅色，或整体走深色高级风；
  **仅定义了 `dark_palette` 的样式（Midnight Business / Ocean Tech）强制深色封面/结论**，
  其余样式深色页需校验对比度。
- **一个可识别但克制的视觉母题（motif）**：在封面、章节、代表性内容页和结尾重复；
  数据页、长图页、引文页可采用更适合内容的轮廓，不要求逐页出现。
- **禁止 AI 痕迹**：标题下划线、装饰性色条/强调条/单侧边框都禁用；用留白、背景色或图标
  区分卡片。
- **安全字体**：正文/任何需要判断文字适配的元素只用 Arial、Calibri、Cambria、Times New
  Roman、Courier New 等（LibreOffice 渲染与 Office 一致）；标题可衬线×正文无衬线组合；
  默认禁止 Aptos。
- **字号**：标题通常 36-44pt，正文中文通常 ≥22pt、英文通常 ≥20pt，说明 10-12pt；
  shared design tokens 的下限为硬底线。放不下时依次压缩文案、调整容器、更换构图、拆页。
- **间距**：0.5" 最小边距、0.3-0.5" 内容块间距；不要让卡片几乎相碰或某侧空一大片。
- **视觉服务内容**：内容页优先采用能解释、比较、举证或组织信息的视觉结构；允许经过
  设计的文字主导页，禁止为达成视觉配额强塞图标、卡片或无关图片。始终避免低对比和溢出。
- **每页的布局选项、数据展示、视觉润色、字号表、间距与 Avoid 清单**见
  `visual-style-menu.md` 的 "Per-Slide Design Ideas"（与 document-skills pptx skill 一致）。

## Create branch

1. 按 Slide Spec 创建 `outputs/.pptx-work/<work-id>/deck.js`；该文件是薄入口，只加载
   Slide Spec、resolved tokens、已验证 asset manifest 并调用 `pptx-composer.js`。
   直接从这些 JSON 输入生成候选稿时，可使用套件入口 `scripts/composer_deck.js`；它只负责
   参数读取、调用 composer 和写出独立候选文件，不绕过 preflight 或 QA。
2. 加载 `pptxgenjs-safety.md`，按官方 gotchas 写 pptxgenjs 脚本；**默认**
   `require("pptx-composer")`：先全 deck preflight，再由 composer 选择共享版式、文字策略、
   形状、SVG 角饰与视觉 fallback。自定义构图也不得绕过同一 preflight。每页设
   `slide.background`（canvas 角色）。深色页统一使用 `H.paletteMode(tokens, "dark")`
   返回的页面 token；不得只切背景，也不得先写文字后补救坐标。
3. deck.js 从 `process.argv[2]` 接收输出路径；每个输出只创建一个 pptxgen 实例。
4. 执行：

   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/scripts/run_with_pptxgenjs.js" --output <candidate.pptx> <deck.js>
   python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_tool.py" validate <candidate.pptx> \
     --output <candidate-stem>-package-report.json --json
   ```

5. wrapper 在原子落盘前只运行 `normalize-generated`（修复 chart axId/presentation 语义），
   不输出 static report，也不做静态门禁。QA 和 delivery 绑定
   `<candidate-stem>-package-report.json`；文字溢出、重叠、可读性问题按 `pptx-qa.md`
   第 3 节做**默认必做**的整套渲染+目检。发现问题时修复 spec/composer/generator 后重建
   整份 candidate，禁止对已打包文件做逐项补丁；重建直接走唯一一次返工边
   `workflow_guard.py transition --to producing --reason <blocker 摘要>`，无需 reset。
   candidate hash 改变后重新执行 content、package 和整套 render；第二次仍有 blocker 时
   转为 `incomplete`。

## Edit branch

严格按 `pptx-editing.md`：inspect/thumbnail -> unpack -> 所有结构操作 -> 内容/样式修改
-> clean -> pack -> `validate --original --output <package-report>`。不得无条件编写 deck.js，也不得调用会原位覆盖
source 的 vendor CLI。

## Rebuild branch

记录 source hash、无法安全编辑的原因、保留项如何迁移，以及与 edit contract 的差异。
之后执行 create branch，并强制生成 change summary。

## Transition to QA

生产完成只代表获得 candidate。`build_support_outputs.py` 仅按已确认 deliverables 生成
speaker notes、full script、teleprompter、training cards 和 references；preview、contact sheet
与 PDF 统一由 render/export 流程生成。完成这些产物后转为 `qa`，再执行 `pptx-qa.md`；此时不得提前对用户
声称文件 ready-to-present。
