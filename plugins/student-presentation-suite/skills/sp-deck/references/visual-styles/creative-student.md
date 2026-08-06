# Creative Student（学生创意）

Best for innovation projects, design topics, campus-life topics, and light classroom showcases.

- **Palette:** `F97316` warm orange accent dominant, `0EA5E9` sky blue secondary, neutral base (`F7F4EF` canvas, `FFFFFF` surface).
- **Visual character:** 每页一个学生真实场景/原型图（`addAnnotatedVisual`）作为锚点，配一处干净解释块；手绘风格只用于注释与箭头，不放正文。
- **Use when:** innovation project, design topic, campus-life topic, product idea, light showcase, reflection report.
- **Creative freedom:** story slides, user journeys, scene images, before/after sections, concept diagrams, playful section markers, expressive but readable titles.
- **Guardrails:** warm accent plus neutral base, not over-saturated, 图片上文字需保证可读（panel 或半透明遮罩）, meaningful visuals only.
- **Typography:** approachable sans-serif body (Arial/Calibri) with one playful title treatment; keep body and technical labels conventional; reserve Cambria/Bookman Old Style only where a humanist heading fits.
- **Slide rhythm:** personal hook, real student scenario, problem, idea/workflow, prototype or example, reflection and next step.
- **Charts and diagrams:** hand-drawn-feeling annotations may frame otherwise clean journeys, comparisons, or concept diagrams.
- **Layout motif:** numbered story panels, journey rows, round icon chips, 同一手绘母题可出现在流程/旅程页（贯穿全 deck）.
- **Fallback layout:** one student-specific scene or example paired with a clean explanation block.
- **Color roles:** canvas `F7F4EF`; surface `FFFFFF`; primary text `1F2937`; secondary text `596273`; primary accent `F97316`; secondary accent `0EA5E9`.
- **Geometry:** 6-8% margins, mixed corners（`corner_radius_pt`=16，`H.cornerRadius(tokens)`）, one playful motif such as tabs or hand-drawn arrows, but align all core content to a stable grid.
- **Slide recipes:** cover = personal hook + project artifact; problem = real campus scenario; idea = before/after or journey; prototype = large visual + annotations; reflection = lessons/limits/next step.
- **Image treatment:** prioritize the student's own photos, sketches, prototypes, screenshots, and process evidence; generated visuals must look illustrative rather than falsely documentary.
- **Density control:** one playful device per slide, no more than four icon/label elements, and 内容页以项目实证为主，不强设 deck 级占比.
- **Acceptance checks:** replace any generic startup or AI wording with real course, team, user, failure, iteration, or observation details.
- **Do not sacrifice:** topic evidence, student-specific detail, speaking clarity, image/source appropriateness.
- **Avoid:** decorative stock images, overdesigned covers, crowded stickers/icons, entertainment style that weakens the argument.

## 通用设计原则（对齐 document-skills pptx skill）

- 本样式是一套 token/recipe；布局与视觉决策遵循 `pptx-production.md` 的 "Visual design"
  节：主导色占 60-70%、默认深色封面/结论页 + 浅色内容页（sandwich，或整体深色高级风；
  **仅定义了 `dark_palette` 的样式强制深色封面/结论**，其余样式深色页需校验对比度）、
  贯穿 deck 的单一母题、安全字体白名单（Arial/Calibri/Cambria/Times New Roman 等）、
  标题 36-44pt（≥token 24pt 下限）、正文 中文 ≥22pt / 英文 ≥20pt（叠加 token 下限）、
  说明/图注 10-12pt、0.5" 最小边距。
- 每个 **content 页**要有视觉元素（图/表/图标/形状）；封面/章节/引文/参考文献/附录/Q&A
  页不强制装饰（对齐 `visual-style-menu.md`）。
- 页面→视觉组件映射见 `visual-style-menu.md` 的"生成指引"表。
- 禁止：标题下划线、装饰性色条/强调条/单侧边框、纯文字 content 页、低对比文字、默认 Aptos。
- 生成时默认用 `H.safeArea` 划分三层 + `V.renderVisual`（按生成指引表选 family）。