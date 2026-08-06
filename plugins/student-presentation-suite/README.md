# Student Presentation Suite for Claude Code

[中文](README-zh.md) | English

`student-presentation-suite` is a Claude Code plugin for student-owned
university presentations. It separates content planning, editable PPTX
production, and existing-deck review while sharing one intake, Slide Spec, and
quality contract.

This plugin is installed as part of the `claude-plugins` repository. See the
[root README](../../README.md) for installation instructions.

Install ID: `student-presentation-suite@claude-personal`.

## Skills

### `sp-outline`

Use for slide outlines, presentation spines, speaking notes, group allocation,
transitions, Q&A preparation, and optional Slide Spec handoff. It never creates
or claims to create a PPTX.

### `sp-deck`

Use for a new editable PPTX or a separate improved copy of an existing deck.
Low-level package editing, validation, and rendering use the suite-owned
`scripts/pptx_tool.py` facade and `shared/pptx_runtime/`. The plugin does not
load an external `document-skills` installation or distribute its copied code.
It deep-clones mutable slide dependencies, runs Open XML SDK markup/schema validation plus
suite-owned package/presentation semantics, and generates hidden-slide-aware paginated contact sheets.
Cleanup is transactional, inspection returns versioned slide metadata, and Linux rendering builds
the bundled AF_UNIX shim only when runtime detection proves the sandbox requires it.

### `sp-review`

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
missing field receives a recommendation and impact statement. Quality level
defaults to `high-score` and citation style to classroom citations — neither is
asked during intake. A user delegation such as “you decide” fills
recommendations but still requires approval of the complete Production Summary,
confirmed via `AskUserQuestion` (confirm / adjust / change style).

Production follows:

`intake_pending → intake_confirmed → planned → producing → qa → complete`

No environment, generation, rendering, or delivery command may run while the
state is `intake_pending`.

The suite records this gate with `workflow_guard.py` state commands
(init/confirm/transition); production runs follow the workflow convention
maintained by SKILL text self-discipline — the PreToolUse hook is removed, so
commands are no longer intercepted automatically.

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
- `<topic>-presentation-package-report.json` from suite validation and reused
- `<topic>-qa-manifest.json` bound to Slide Spec evidence and the delivered PPTX
- `<topic>-delivery-report.json` with final gate evidence
- `<topic>-change-summary.md` for existing-deck improvements
- requested PDF, HTML teleprompter, training cards, references, quality report,
  and revision manifest

The plugin installation directory is read-only for user deliverables.

## Visual System

The PPTX skill first reads `skills/sp-deck/references/visual-style-menu.md`, recommends the strongest
topic-fit choices, then loads exactly one style specification from
`visual-styles/`. Each style defines color roles, typography, geometry, layout
recipes, image treatment, density limits, and acceptance checks.

Styles are directions rather than fixed templates. Layout must follow the
slide's function, and decorative visuals must not replace evidence or
readability.

`deck.js` is written as raw pptxgenjs following the official generation
gotchas in `skills/sp-deck/references/pptxgenjs-safety.md`. `pptx-helpers.js`/`pptx-visuals.js`/`pptx-icons.js`
are optional conveniences; `pptx-visuals.js` implements editable layout families
(hero, visual-dominant, process-path, timeline, comparison, dashboard,
architecture, matrix, quote, summary, reference) with shapes, connectors, labels,
contained images, accessible alt text, and projection-readable charts.

## Quality Gates

PPTX delivery requires:

- environment compatibility check;
- Slide Spec validation when supplied;
- editable PPTX generation (raw pptxgenjs following the official gotchas);
- speaker notes;
- text extraction sanity check for edit/template-derived decks;
- a QA manifest that binds the source Slide Spec hash and matches its Slide Spec/PPTX/package-report hashes（spec 自规划期未被改动时不再重复校验）;
- a package report using the complete suite validation profile with successful Open XML schema validation;
- requested quality reports bound to the source Slide Spec or current PPTX hash;
- resolved design tokens when a standard visual style is selected;
- strict delivery-check success;
- separate change summary for an improved existing deck.

Per-page render + visual inspection is a default single fast loop (render all →
inspect → fix only the changed slides → re-render only those pages); a QA blocker
is fixed via the rework edge
`workflow_guard.py transition --to producing --reason <blocker summary>` instead
of resetting the whole pipeline.

Results use `complete`, `incomplete`, or `blocked`. `complete` additionally
requires `workflow_guard.py transition --to complete --pptx <pptx> --qa-manifest <manifest>
--delivery-report <report>`. The PptxGenJS wrapper
normalizes the generated package and atomically publishes it; layout/overflow quality
is caught by QA visual inspection and package validation.
QA and delivery reuse the package report instead of revalidating an unchanged deck.
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
python scripts/check_claude_pptx_env.py --mode edit_ooxml --json --strict
python scripts/pptx_tool.py --help
python scripts/validate_slide_spec.py path\to\spec.yaml --json
python scripts/validate_presentation_brief.py path\to\brief.yaml --json
python scripts/analyze_presentation_spec.py path\to\spec.yaml --strict --json
python scripts/build_support_outputs.py path\to\spec.yaml --output-dir <project>\outputs --json
python scripts/create_revision_manifest.py old.yaml new.yaml --strict
python scripts/manage_versions.py snapshot --output-root <project>\outputs --revision-id r1 --file <deck>
python scripts/slide_spec_to_pptx_brief.py path\to\spec.yaml --output-dir <project>\outputs
python scripts/bump_version.py 0.5.0 --dry-run  # 统一版本升级
node scripts/run_with_pptxgenjs.js --probe
python scripts/smoke_pptx.py
```

## Environment Variables

The plugin relies on two environment variables automatically set by Claude Code:

| Variable | Set by | Purpose |
|----------|--------|---------|
| `${CLAUDE_PLUGIN_ROOT}` | Plugin system | Plugin installation directory; used for script references |
| `${CLAUDE_PROJECT_DIR}` | Runtime | Active project directory; used as the output root for deliverables |

User deliverables are always written under `${CLAUDE_PROJECT_DIR}/outputs`.
When `${CLAUDE_PROJECT_DIR}` is unavailable, the plugin falls back to the
current working directory.

A minimal `.env.example` is included for reference; these variables are
injected at runtime and do not normally need manual configuration.

## Package Boundary

This is a Claude Code package. It intentionally contains no `.codex-plugin`,
`agents/openai.yaml`, `artifact-tool`, or Codex runtime declaration.

### Open XML SDK Validation

The suite includes a small .NET adapter at
`shared/pptx_runtime/openxml_validator/` that wraps
`DocumentFormat.OpenXml` 3.5.1 for PPTX markup/schema validation. Build with:

```powershell
dotnet restore shared/pptx_runtime/openxml_validator/OpenXmlValidator.csproj
dotnet build shared/pptx_runtime/openxml_validator/OpenXmlValidator.csproj
```

This is a suite-owned implementation; no ECMA/ISO XSD files from the
`document-skills` upstream are copied or distributed. See
`references/pptx-runtime-provenance.md` for the full audit record.

See the repository [README](../../README.md), [AGENTS.md](../../AGENTS.md), and
[CHANGELOG.md](../../CHANGELOG.md) for installation, maintenance, and releases.
