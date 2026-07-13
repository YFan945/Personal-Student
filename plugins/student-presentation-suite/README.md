# Student Presentation Suite for Claude Code

[中文](README-zh.md) | English

`student-presentation-suite` is a Claude Code plugin for student-owned
university presentations. It separates content planning, editable PPTX
production, and existing-deck review while sharing one intake, Slide Spec, and
quality contract.

Install ID: `student-presentation-suite@claude-personal`.

## Skills

### `student-presentation`

Use for slide outlines, presentation spines, speaking notes, group allocation,
transitions, Q&A preparation, and optional Slide Spec handoff. It never creates
or claims to create a PPTX.

### `student-presentation-ppt`

Use for a new editable PPTX or a separate improved copy of an existing deck.
Low-level generation and editing come from
`document-skills@anthropic-agent-skills`; this plugin supplies the student
workflow, confirmed requirements, style controls, outputs, and QA gates.

### `student-presentation-review`

Use for review, scoring, diagnosis, planned-vs-actual comparison, and concrete
slide fixes. Review is read-only by default. “Fix it directly” first produces a
diagnosis, then hands structured findings into the PPTX skill.

## Full PPTX Intake

Before production, confirm:

- topic;
- course/context and presentation type;
- audience and language;
- duration and slide count;
- individual/group format and members;
- rubric or required sections;
- source material and evidence boundaries;
- template, logo, or branding constraints;
- image-source strategy;
- visual style;
- required deliverables.

The plugin reuses confirmed information and asks only for missing fields. Each
missing field receives a recommendation and impact statement. A user delegation
such as “you decide” fills recommendations but still requires approval of the
complete Production Summary.

Production follows:

`intake_pending → intake_confirmed → planned → producing → qa → complete`

No environment, generation, rendering, or delivery command may run while the
state is `intake_pending`.

The plugin ships a `PreToolUse` hook and `workflow_guard.py`. Suite production
commands are denied until an approved Production Summary hash moves the project
state to `intake_confirmed`.

## Structured Handoff

Slide Spec YAML carries confirmed planning data into PPTX production. Its `meta`
supports topic, presentation type, audience, language, timing, ownership,
course, rubric, source material, template, image policy, visual style,
deliverables, and output prefix.

Existing-deck improvement additionally uses:

- `source_deck`
- `edit_intent`
- `review_findings`
- `preserve`
- `change_summary_required`

The original source deck is never overwritten.

Slide Spec v2 additionally carries scenario, audience depth, structure mode,
quality controls, layered slide copy/notes, Evidence Ledger references, locked
slides, and revision metadata. Legacy Slide Spec remains accepted.

## Outputs

Deliverables are written under `${CLAUDE_PROJECT_DIR}/outputs`, or the current
project's `outputs/` directory when the environment variable is unavailable:

- `<topic>-presentation.pptx`
- `<topic>-speaker-notes.md`
- `<topic>-preview.png` or contact sheet
- `<topic>-qa-manifest.json` bound to the delivered PPTX and rendered previews
- `<topic>-style-adherence-report.json` for the selected visual style
- `<topic>-delivery-report.json` with final gate evidence
- `<topic>-change-summary.md` for existing-deck improvements
- requested PDF, HTML teleprompter, training cards, references, quality report,
  and revision manifest

The plugin installation directory is read-only for user deliverables.

## Visual System

The PPTX skill first reads `visual-style-menu.md`, recommends the strongest
topic-fit choices, then loads exactly one style specification from
`visual-styles/`. Each style defines color roles, typography, geometry, layout
recipes, image treatment, density limits, and acceptance checks.

Styles are directions rather than fixed templates. Layout must follow the
slide's function, and decorative visuals must not replace evidence or
readability.

## Quality Gates

PPTX delivery requires:

- environment compatibility check;
- Slide Spec validation when supplied;
- editable PPTX generation;
- speaker notes;
- text extraction sanity check;
- LibreOffice rendering and Poppler page images;
- visual inspection and at least one fix-and-verify loop;
- a QA manifest with matching PPTX/preview hashes, full slide coverage, and zero blockers;
- resolved design tokens and a style-adherence report when a standard visual style is selected;
- strict delivery-check success;
- separate change summary for an improved existing deck.

Results use `complete`, `incomplete`, or `blocked`. `complete` additionally
requires `workflow_guard.py transition --to complete --pptx <pptx> --qa-manifest <manifest>`.
Static XML findings alone are not proof of rendered clipping or readability.
CI also creates and renders a temporary scenario matrix for coursework, English
classroom, defense, competition, club showcase, research, software project,
data survey, and school-template editing; no generated deck or preview is
committed to the repository.

## Runtime

Claude Code does not automatically install this package's Python or Node runtime
dependencies. Use the repository-level installer or install manually:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-claude-pptx.txt
npm ci
```

Useful checks:

```powershell
python scripts/check_claude_pptx_env.py --json --strict
python scripts/validate_slide_spec.py path\to\spec.yaml --json
python scripts/validate_presentation_brief.py path\to\brief.yaml --json
python scripts/analyze_presentation_spec.py path\to\spec.yaml --strict --json
python scripts/build_support_outputs.py path\to\spec.yaml --output-dir <project>\outputs --json
python scripts/create_revision_manifest.py old.yaml new.yaml --strict
python scripts/manage_versions.py snapshot --output-root <project>\outputs --revision-id r1 --file <deck>
python scripts/slide_spec_to_pptx_brief.py path\to\spec.yaml --output-dir <project>\outputs
node scripts/run_with_pptxgenjs.js --probe
python scripts/smoke_pptx.py
```

## Package Boundary

This is a Claude Code package. It intentionally contains no `.codex-plugin`,
`agents/openai.yaml`, `artifact-tool`, or Codex runtime declaration.

See the repository [README](../../README.md), [AGENTS.md](../../AGENTS.md), and
[CHANGELOG.md](../../CHANGELOG.md) for installation, maintenance, and releases.
