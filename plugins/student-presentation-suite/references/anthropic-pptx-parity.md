# Anthropic PPTX Workflow Parity

本矩阵记录行为对齐，不表示复制、打包或运行外部缓存。实现均为 suite-owned。

| Baseline behavior | Suite-owned implementation | Evidence |
| --- | --- | --- |
| Create uses PptxGenJS | wrapper + controlled composer | composer/helper tests and create scenarios |
| Edit/template begins with text and thumbnail inspection | inspect → thumbnail → unpack | editing contract and scenario matrix |
| Structural edits precede content edits | add/delete/reorder before replacements | OOXML scenario and command tests |
| Clean before repack | clean → pack | package edit tests |
| Template validation uses original baseline | `validate --original` | template-derived scenario |
| Content QA | `content-qa` binds full text, notes, placeholders, order and spec | QA command tests |
| File QA | Open XML SDK + suite semantic validation | package report profile v4 |
| Visual QA | full render + explicit page findings | `visual-inspection` and QA manifest hashes |
| Fix generator, not final PPTX | one full rebuild loop | workflow guard and production contract |
| Safe fonts and PptxGenJS gotchas | safety contract + lint/tests | safety and release checks |

每次 candidate hash 变化后都重新运行 content QA、package validation 和整套渲染。
人工复核可重点查看变更页和相邻页，但报告必须覆盖全部页面。第二次返工请求被拒绝；仍有
blocker 时状态转为 `incomplete`。
