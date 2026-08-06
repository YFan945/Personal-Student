# Sage Calm（鼠尾草平静）

Best for wellness, counseling, learning habits, mental health education, and low-stress reports.

- **Palette:** `84B59F` sage dominant, `69A297` eucalyptus secondary, `50808E` slate accent.
- **Visual character:** 每页一个舒缓的主流程/清单 + 具体行动；`primary_accent` `84B59F` 用于进度/重点，正文深石板字；留白充足，情绪化视觉必须支撑具体行动。
- **Use when:** wellness report, learning method, counseling education, habit design, reflective self-improvement.
- **Creative freedom:** gentle process steps, self-assessment diagrams, habit loops, calm section pages, simple icons.
- **Guardrails:** calm surfaces kept classroom-readable; pale surfaces retain strong contrast; 每页聚焦一个主流程/清单.
- **Typography:** calm humanist sans-serif body (Arial/Calibri), medium-weight titles, generous line spacing, dark slate text for contrast; serif (Cambria/Bookman Old Style) only where a humanist heading fits.
- **Slide rhythm:** relatable situation, causes or behavior loop, practical method, small actionable steps, measured reflection.
- **Charts and diagrams:** habit loops, self-assessment scales, simple timelines, and low-noise before/after comparisons.
- **Layout motif:** airy spacing, rounded panels, soft section labels, low-noise diagrams.
- **Fallback layout:** one calm process or checklist with concrete actions; avoid empty wellness imagery.
- **Color roles:** canvas `F4F7F2`; surface `FFFFFF`; primary text `263D3A`; secondary text `5C716D`; primary accent `84B59F`; secondary accent `69A297`.
- **Geometry:** 8-10% margins, soft rounded corners（`corner_radius_pt`=16，`H.cornerRadius(tokens)`）, 柔和同色系 section band（与内容保持对比度）, generous line spacing, simple circular or loop geometry.
- **Slide recipes:** cover = relatable question or observation; cause = behavior loop; method = 3-5 gentle steps; practice = checklist/timeline; reflection = progress + limitation.
- **Image treatment:** use quiet real-life contexts, simple illustrations, or self-assessment diagrams; avoid spa imagery, staged meditation clichés, or unsupported clinical claims.
- **Density control:** 每页聚焦一个主流程/清单, three primary actions maximum, minimal badges, and no decorative botanical clusters.
- **Acceptance checks:** every calming visual must support a concrete action or explanation; all pale surfaces must retain classroom contrast.
- **Do not sacrifice:** concrete action steps, psychological accuracy, projection contrast.
- **Avoid:** spa-like decoration, pale text on pale backgrounds, slides that feel too empty.

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