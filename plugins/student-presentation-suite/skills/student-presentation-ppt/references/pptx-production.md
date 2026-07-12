# PPTX Production

Load `../../../references/presentation-intake.md` for the complete intake gate and
workflow states. Load `../../../references/shared-standards.md` for readability,
language, anti-AI wording, and group rules. Load
`../../../references/image-strategy.md` for source choices. Load
`visual-style-menu.md`, then only the selected `visual-styles/<style>.md`.
Load `../../../references/presentation-brief.md`,
`../../../references/content-workflow.md`,
`../../../references/evidence-and-citations.md`, and
`../../../references/revision-training-export.md` only when those capabilities
are requested.

Do not use this reference to bypass intake. Production begins only after the
complete Production Summary is explicitly confirmed.

## Build Sequence

1. Read confirmed constraints from the approved Production Summary or Slide Spec meta; never silently replace them.
2. Use the confirmed creative direction. If the summary delegated style choice, select the strongest topic-fit option recorded there.
3. Generate or absorb Slide Spec structure. Use the layered order: directory, claim/points, PPT copy, speaker version, then Slide Spec. Preserve slide order, ownership, timing, visual purpose, evidence refs, locks, and handoff intent unless changing an unlocked item prevents crowding or improves clarity. If the Slide Spec includes `source_deck`, `edit_intent`, `review_findings`, `preserve`, or `change_summary_required`, treat those fields as the programmatic handoff from review to PPTX production.
4. For existing deck improvement, convert review findings into a brief edit plan first. Preserve useful content and required template elements, decide which slides are rewritten vs redesigned, and write the improved deck to a new filename instead of overwriting the source. When `change_summary_required` is true, do not finish without `outputs/<topic>-change-summary.md` or an explicit limitation.
5. Design the PPTX with variation inside guardrails. Layouts should express a function, not force a repeated template. Use topic-specific examples, visuals, chart forms, section rhythm, and opening/closing treatment. Keep a mismatch ledger while building: record any difference between requested constraints and the working assumptions, any missing source material, and any tool/API behavior discovered during production.
6. Run `analyze_presentation_spec.py` and resolve Critical/Major story, density, and evidence findings before production. Run delivery checks for every requested export. Static XML risk counts are not enough on their own: distinguish true production blockers from expected small footer, page marker, caption, source, or kicker text.
7. Confirm visual QA. Preview/contact sheet review is required before calling a deck ready-to-present; otherwise say the file is generated but visual QA is incomplete. If the first render shows geometry mismatch, blank slides, text collapsed into the corner, overlap, or clipped callouts, fix the slide code and rerender before delivery.

## Creativity Rules

- Do not make every slide a card grid. Vary structure based on meaning: process, contrast, evidence, story, risk, recommendation, or Q&A.
- Do not use visual effects as decoration. Each image, shape, panel, timeline, chart, or callout must clarify the slide's main claim.
- Keep the deck subject-specific. Use course context, project details, survey/result evidence, examples, or scenario language from the user instead of generic filler.
- Style freedom is allowed in composition, section pacing, cover treatment, diagrams, color accents, and visual metaphors, but not in readability, source safety, or delivery verification.
- State the chosen direction and why it fits. Do not treat a preset as a fixed template.

## Output Naming

Use topic-specific filenames under `outputs/`:
- `outputs/<topic>-presentation.pptx`
- `outputs/<topic>-speaker-notes.md`
- `outputs/<topic>-preview.png` or a generated contact sheet
- `outputs/<topic>-change-summary.md` when improving an existing deck
- requested `outputs/<topic>-presentation.pdf`
- requested `outputs/<topic>-teleprompter.html`
- requested `outputs/<topic>-quality-report.json`
- requested `outputs/<topic>-revision-manifest.json`
- versioned copies under `outputs/versions/<revision-id>/`

If Slide Spec meta includes `output_prefix`, use it as the `<topic>` slug; otherwise derive a short ASCII-safe slug from the topic. Write deliverables under `${CLAUDE_PROJECT_DIR}/outputs` or the current project fallback. Keep final response paths absolute and never write deliverables into `${CLAUDE_PLUGIN_ROOT}`.

## Classroom Readability

### Typography Thresholds

Check:
- title is readable from the back of a classroom
- Chinese normal body text is 22pt or larger
- English normal body text is 20pt or larger
- smaller text appears only in minor explanations, captions, citations, footnotes, or chart axes when unavoidable
- slide titles, subtitles, section headers, card headers, chart titles, panel labels, and other subheadings are 24pt or larger
- key terms are visually emphasized with bold, accent color, larger type, or callouts

### Text Fit: Preventing Overflow At Minimum Font Sizes

**The minimum font sizes (22pt Chinese / 20pt English / 24pt title) are hard constraints for classroom readability. Text must fit its container at these sizes.** When text at minimum size would overflow the box, the fix is to reduce content or split slides — never to shrink below the minimums.

**Estimation formula** (use before writing pptxgenjs code):

```
char_width_cm  = font_size_pt × 0.035  (Chinese) or 0.021 (English avg)
chars_per_line = floor(box_width_cm / char_width_cm)
est_lines      = ceil(total_chars / chars_per_line)
line_height_cm = font_size_pt × 1.4 / 72 × 2.54
text_height_cm = est_lines × line_height_cm
```

**Overflow threshold**: if `text_height_cm > box_height_cm × 0.85`, the text is likely to overflow or clip.

**Quick reference** (Chinese text, 22pt, with typical padding):

| Box width | Chars/line | 80 chars needs | 120 chars needs |
|-----------|-----------|----------------|-----------------|
| 8 cm      | ~10       | 8 lines × 1.1cm = 8.8cm | DO NOT USE — split slide |
| 10 cm     | ~13       | 7 lines × 1.1cm = 7.7cm | DO NOT USE — split slide |
| 12 cm     | ~15       | 6 lines × 1.1cm = 6.6cm | 8 lines = 8.8cm |
| 14 cm     | ~18       | 5 lines × 1.1cm = 5.5cm | 7 lines = 7.7cm |

**When text does not fit at minimum font size (in priority order):**
1. **Split the slide** — one claim per slide, move details to a second slide
2. **Reduce content** — cut filler words, move explanation to speaker notes
3. **Enlarge the text box** — if layout allows without breaking alignment
4. **NEVER** shrink below 22pt Chinese / 20pt English / 24pt title

**For pptxgenjs**: set `fontSize` to the minimum values above. Do not rely on `autoFit: true` or `shrinkText: true` — these behave inconsistently across PowerPoint, WPS, and LibreOffice. If text needs shrinking to fit, the content or layout is wrong.

**During QA**: when a box's estimated text height exceeds 85% of the box height, the delivery check will flag `text-vertical-overflow-risk`. This is a Major finding that must be resolved before delivery.
- contrast is high
- slide is understandable in 3 seconds
- no dense paragraph blocks
- no decorative objects fighting the main message
- no text overflow, clipping, or text touching the edge of its box
- use a portable font family or define a tested fallback; flag uncommon explicit
  fonts for compatibility review across PowerPoint, WPS, Windows, and macOS

## Content Quality

Every content slide should have one message and a clear visual or structural focus when that helps explain the message. Argumentative and evidence slides should normally use claim-style titles. Covers, section dividers, quotation slides, references, appendix, and Q&A slides may use descriptive titles and may omit speaker-note goals, transitions, or additional visuals when those elements would be artificial. Move explanation into speaker notes instead of shrinking slide text. Avoid pages that look empty because they only contain a title and one vague sentence.

Use concrete examples, data, diagrams, process steps, comparisons, or case details. Use shape-based structure such as panels, cards, dividers, process nodes, timeline blocks, callouts, or section bands. Use translucent panels or simulated glassmorphism only when they make text easier to read; fall back to opaque panels if PPTX/WPS rendering is weak.

For data slides: one chart/table only, one conclusion sentence, no unexplained raw data.
Numeric, causal, survey, experiment, quotation, and case claims must map to the
Evidence Ledger or be explicitly labeled as assumptions/illustrations.
For defense decks: include objective, method/work, result, reflection, and Q&A.
For group decks: include member assignment and handoff lines.
For general undergraduate English decks: use B1-B2 as the default reference point, 2-4 short sentences per content slide, natural connectors in notes, and pronunciation/glossary help when useful. Adjust language level for advanced courses, disciplinary terminology, audience, and speaker ability.

## Image Handling

Follow `../../../references/image-strategy.md`. Use images or meaningful visuals on content slides when they explain, evidence, compare, or organize the message. Do not force imagery onto covers, dividers, references, appendix, Q&A, or content that is clearer as text. Respect requests for text-only, diagram-only, no network, or no generated assets. Avoid unrelated stock-like decoration. Record source URLs for web images when appropriate.

## Anti-AI Review

Remove or rewrite: generic openings, exaggerated claims, textbook paragraphs, motivational filler, repeated sentence patterns, vague words such as "various", "many aspects", "very important" without specifics.

Prefer: concrete class/project context, simple direct claims, examples from student life or source material, modest but clear conclusions.

## Claude Code PPTX Production and Priority

Claude Code PPTX production depends on `document-skills@anthropic-agent-skills`. Its `pptx` skill owns the low-level generation and editing mechanics. This suite owns the student-context route, classroom typography, Slide Spec, output location, notes, change summary, and delivery gate. When generic upstream advice conflicts with these requirements, this suite takes priority.

When building in Claude Code:
- Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/check_claude_pptx_env.py" --json --strict` before production. Missing required tools make production `blocked`.
- For Slide Spec input, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/slide_spec_to_pptx_brief.py" <spec> --output-dir "${CLAUDE_PROJECT_DIR}/outputs" --output "${CLAUDE_PROJECT_DIR}/outputs/<topic>-claude-pptx-brief.md"`. When `CLAUDE_PROJECT_DIR` is unavailable, substitute the current project directory.
- First follow the `pptx` skill's `SKILL.md`.
- For a new deck from scratch, read and follow `pptxgenjs.md`.
- For editing an existing PPTX or template, read and follow `editing.md`.
- Keep this student-presentation skill as the upper-level brief: confirmed classroom constraints, Slide Spec, creative direction, readability, notes, anti-AI wording review, and final QA contract still apply.

Required QA inherited from the `pptx` skill:
- Run `python -m markitdown output.pptx` for content extraction and sanity checking.
- Render the deck with the `pptx` skill's LibreOffice helper, then convert PDF pages to images with Poppler, for example `scripts/office/soffice.py` plus `pdftoppm`.
- Inspect rendered images or a contact sheet and complete at least one fix-and-verify loop before calling the deck ready-to-present.
- Run generated deck JavaScript with `node "${CLAUDE_PLUGIN_ROOT}/scripts/run_with_pptxgenjs.js" <deck-script.js>`.
- Run `python "${CLAUDE_PLUGIN_ROOT}/skills/student-presentation-ppt/scripts/pptx_delivery_check.py" --pptx <pptx> --notes <notes> --preview <preview> --strict --json`. A failed gate makes delivery `incomplete`.
- Add `--pdf`, `--teleprompter`, `--quality-report`, and
  `--revision-manifest` when those exports were confirmed.
- For revisions, run `create_revision_manifest.py <old-spec> <new-spec> --strict`;
  any locked-slide change blocks delivery until the user explicitly unlocks it.
- For teleprompter, training cards, or references, run
  `build_support_outputs.py <spec> --output-dir <outputs> --json`.
- When versioning is enabled, snapshot confirmed deliverables with
  `manage_versions.py snapshot`; use `restore` to create a non-destructive
  rollback candidate.

Dependencies and limitations:
- The Claude plugin dependency is `document-skills`, not the standalone `pptx` skill path.
- The expected install target is `document-skills@anthropic-agent-skills`; if the local plugin is named differently, use the actual name from the marketplace manifest.
- The `pptx` skill expects environment tools such as `pptxgenjs`, `markitdown[pptx]`, Pillow, LibreOffice, and Poppler. If any are unavailable, report the missing QA or generation step explicitly.
- The `pptx` skill does not natively enforce this suite's Slide Spec schema. Use `slide_spec_to_pptx_brief.py` as the programmatic bridge: it validates the schema and converts the Slide Spec into a Claude `pptx` production brief, including existing-deck improvement fields such as `source_deck`, `edit_intent`, `review_findings`, `preserve`, and `change_summary_required`. The final generation still depends on the `pptx` skill following that brief.

## Final Deliverable QA

Before final response:
- confirm `.pptx` exists and filename is topic-specific
- run the `${CLAUDE_PLUGIN_ROOT}` delivery-check command above and require it to pass
- render and inspect at least the contact sheet or preview images
- verify Chinese normal body text >= 22pt, English normal body text >= 20pt, and primary slide titles normally >= 24pt; visually verify any smaller secondary labels
- verify important keywords are visually emphasized
- verify no text is out of frame, clipped, overflowing, or too close to box edges
- verify layouts are neither too empty nor too crowded
- verify images support the argument and are not decorative filler
- verify content slides have enough hierarchy to communicate clearly; do not add shapes, panels, cards, or diagrams solely to satisfy a structural-layer rule
- verify background shapes or translucent panels improve hierarchy without reducing readability
- verify text is not placed directly over busy images unless a sufficiently opaque panel protects readability
- create a separate script/notes file if speaker notes are not embedded
- for improved existing decks, create a change summary that lists kept content, changed slides, unresolved issues, and QA results
- report any missing expected file and validation limitations honestly
- list `Known Issues to Fix` and `Before Presenting` when any validation, source, timing, or visual issue remains

## Final Response Contract

```markdown
## Generated Files
- PPTX: <absolute path> exists=<true|false>
- Notes: <absolute path or not created> exists=<true|false|n/a>
- Preview/Contact Sheet: <absolute path or not created> exists=<true|false|n/a>

## Deck Summary
- Slides:
- Duration:
- Language:
- Group order:

## Creative Direction
- Direction:
- Why it fits:
- Main visual choices:

## QA
- Delivery check:
- Static XML risks:
- Visual QA:
- Limitations:
- Known Issues to Fix:
- Before Presenting:
```
