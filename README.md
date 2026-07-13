# Student Presentation Suite for Claude Code

[中文](README-zh.md) | English

> This branch is built specifically for **Claude Code**. Its installation,
> dependencies, and runtime behavior are not intended for Codex. If you use
> **OpenAI Codex**, see the
> [`main` branch](https://github.com/YFan945/student-presentation-suite/tree/main)
> instead.

`student-presentation-suite` supports student-owned university presentations,
including coursework reports, thesis defenses, and group presentations. In
Claude Code it can plan an outline and speaker notes, create an editable PPTX,
review an existing deck, or produce a separate improved version.

Plugin install ID:

```text
student-presentation-suite@claude-personal
```

The current PPT generation quality controls and known enforcement gaps are
documented in [PPT-GENERATION-QUALITY-AUDIT.md](PPT-GENERATION-QUALITY-AUDIT.md).

## Features

| Request | Skill | Result |
| --- | --- | --- |
| Outline, slide content, notes, or group allocation | `student-presentation` | Markdown planning documents; no PPTX |
| Create, rebuild, or edit an editable PPT/PPTX | `student-presentation-ppt` | PPTX, speaker notes, and preview |
| Review, score, or diagnose an existing deck | `student-presentation-review` | Read-only review by default |

PPTX creation and editing depend on
`document-skills@anthropic-agent-skills`, which the installer also installs.

## Structured Workflow And Controls

Version 0.4 adds a confirmed Presentation Brief before Slide Spec/PPTX work:

- automatic classification for coursework, defense, competition, club showcase, and research;
- audience type and explanation depth;
- problem-solution, research, timeline, comparison, case-study, and product structures;
- beginner/expert interaction and basic/high-score quality modes;
- per-slide text limits, visual/text ratio, notes, key lines, citation style, exports, and versioning;
- layered generation: directory → slide claims → PPT copy → speaker version → Slide Spec;
- Evidence Ledger, deterministic quality report, locked slides, revision manifests, training cards, and rehearsal support.

Local exports can include PPTX, PDF, previews, Markdown notes, HTML teleprompter,
quality report, references, and revision manifest. Web editing and cloud
synchronization require an external service and are not claimed by this plugin.

## Requirements

Install these tools first:

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Git
- Python 3.10+
- Node.js and npm
- LibreOffice and Poppler (recommended, for rendered QA and PDF export; PPTX generation works without them)

Check the basic commands:

```powershell
claude --version
git --version
python --version
node --version
npm --version
```

## Download And Install

### Recommended Windows Installation

Run in PowerShell:

```powershell
git clone --branch claude-code --single-branch `
  https://github.com/YFan945/student-presentation-suite.git `
  "$env:USERPROFILE\.agents\claude-plugins"

Set-Location "$env:USERPROFILE\.agents\claude-plugins"
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_claude_plugin.ps1 -Migrate
```

`-Migrate` removes the obsolete `student-presentation-suite@personal`
registration and cache, then:

1. installs the Python and Node.js dependencies;
2. registers the local `claude-personal` marketplace;
3. installs `document-skills@anthropic-agent-skills`;
4. installs and enables `student-presentation-suite@claude-personal`;
5. runs the strict environment check and displays plugin status.

Restart Claude Code after installation.

### Existing Checkout

```powershell
Set-Location "$env:USERPROFILE\.agents\claude-plugins"
git switch claude-code
git pull --ff-only origin claude-code
.\scripts\install_claude_plugin.ps1
```

To re-register the plugin without reinstalling dependencies:

```powershell
.\scripts\install_claude_plugin.ps1 -SkipDependencies -SkipMarketplaceClone
```

## Verify The Installation

```powershell
claude plugin marketplace list
claude plugin list
claude plugin details student-presentation-suite@claude-personal
python .\plugins\student-presentation-suite\scripts\check_claude_pptx_env.py --json --strict
```

The results should include:

- marketplace: `claude-personal`
- plugin: `student-presentation-suite@claude-personal`
- upstream dependency: `document-skills@anthropic-agent-skills`

If Claude Code does not discover the plugin immediately after installation or
update, exit Claude Code completely and start it again.

## Usage

Open Claude Code from your coursework project:

```powershell
Set-Location D:\my-course-project
claude
```

Describe the task in natural language. The plugin is intentionally limited to
clear student academic presentation contexts; generic business or marketing
decks do not route into these skills.

Before creating or editing a PPTX, Claude prepares a complete
`Production Summary` covering the topic, course, audience, language, duration,
slide count, rubric, sources, visual style, and deliverables. Production starts
only after you confirm it.

A plugin `PreToolUse` hook enforces this boundary for suite production
commands. The approved summary hash and workflow state are stored in the
project output directory, so the gate does not rely only on model compliance.

Deliverables are written to the active project's `outputs/` directory, never
to the plugin installation. Existing source decks are never overwritten.

## Examples

### 1. Outline And Speaker Notes Only

```text
I am a software engineering student preparing a six-minute course report on
"AI-assisted software testing." Design an eight-slide outline with speaker
notes and timing for each slide. Do not create a PPTX.
```

This produces an outline, slide-level notes, transitions, and optional Q&A.

### 2. Create An Editable PPTX

```text
Create an editable PPTX for my university course.
Topic: "Reflections on Learning Generative AI." Chinese, individual report,
five minutes, eight slides, for my instructor and classmates. Use a clean,
modern style and deliver the PPTX, slide-level notes, and a preview.
```

Claude fills any missing requirements, shows the complete
`Production Summary`, and waits for confirmation before production.

### 3. Group Course Presentation

```text
Our four-person team has a 12-minute database course presentation on
"Consistency in Distributed Databases." Create a 12-slide English PPTX,
assign slides and speaking time to each member, and include speaker notes and
likely instructor questions.
```

The plugin handles ownership, handoffs, timing, and Q&A preparation.

### 4. Thesis Defense

```text
Use the thesis, experiment results, and images in this project to create a
15-slide Chinese PPTX for my undergraduate thesis defense. Keep it within ten
minutes and emphasize the research question, method, results, contributions,
and limitations. Use only my supplied evidence and do not invent data.
```

Place the thesis, data, images, and university template in the project before
starting Claude Code.

### 5. Review An Existing Deck Without Editing

```text
Review outputs\defense.pptx for structure, text density, font size, chart
readability, timing, and defense risks. Report concrete fixes only; do not
modify the source file.
```

The report identifies the target slide, issue, impact, severity, and fix.

### 6. Review And Produce An Improved Copy

```text
Review outputs\course-report.pptx and then create an improved copy.
Preserve the university template, logo, approved data, and citations. Improve
the narrative, layout, and speaker notes, do not overwrite the original, and
provide a change summary.
```

The plugin diagnoses the deck first, confirms the editing requirements, then
creates a separate PPTX and change summary.

## Output Files

Depending on the request, `outputs/` may contain:

```text
<topic>-outline.md
<topic>-presentation.pptx
<topic>-speaker-notes.md
<topic>-preview.png
<topic>-qa-manifest.json
<topic>-style-adherence-report.json
<topic>-delivery-report.json
<topic>-change-summary.md
<topic>-presentation.pdf
<topic>-teleprompter.html
<topic>-training-cards.md
<topic>-quality-report.json
<topic>-revision-manifest.json
```

The final response reports each absolute file path, slide count, rendered QA
result, and the status: `complete`, `incomplete`, or `blocked`. A `complete`
delivery now requires a QA manifest bound to the current PPTX and rendered
preview hashes; it records full-page inspection and zero remaining blockers.
Standard visual styles also resolve to tokenized palette, spacing, typography,
and line constraints, with a style-adherence report available for delivery QA.
The release workflow also renders a temporary scenario matrix on Linux for
coursework, English-classroom, defense, competition, club-showcase, research,
software projects, data surveys, and school-template editing.

## Update And Uninstall

Update the repository and plugin:

```powershell
Set-Location "$env:USERPROFILE\.agents\claude-plugins"
git pull --ff-only origin claude-code
claude plugin update -s user student-presentation-suite@claude-personal
```

Uninstall:

```powershell
claude plugin uninstall student-presentation-suite@claude-personal
claude plugin marketplace remove claude-personal
```

## Troubleshooting

### The Plugin Does Not Trigger

Make the student academic context and presentation intent explicit. You can
also name `student-presentation`, `student-presentation-ppt`, or
`student-presentation-review` directly in the request.

### The Environment Check Fails

Run:

```powershell
python .\plugins\student-presentation-suite\scripts\check_claude_pptx_env.py --json --strict
python .\scripts\check_installed_version.py --json
```

Install the missing Python, Node.js, or `document-skills` dependency reported by
the check. LibreOffice and Poppler are recommended but not required — missing
them skips rendered QA and PDF export but does not block PPTX generation.

### Workflow State Is Stuck

If the plugin blocks production commands because the Production Summary was not
confirmed yet, or the state is stuck in `blocked`:

```powershell
python .\plugins\student-presentation-suite\scripts\workflow_guard.py reset
```

To recover from `blocked` state after fixing a missing dependency:

```powershell
python .\plugins\student-presentation-suite\scripts\workflow_guard.py unblock
```

`unblock` returns the project to `intake_pending`; confirm the Production Summary
again before resuming production.

### Where Are Generated Files?

They are under the project directory from which Claude Code was started:
`outputs/`. If `CLAUDE_PROJECT_DIR` is set, the location is
`${CLAUDE_PROJECT_DIR}/outputs`.

### Can Codex Use This Branch?

No. This branch supports Claude Code only. Use the
[`main` branch](https://github.com/YFan945/student-presentation-suite/tree/main)
for Codex.

## Development And Releases

See [AGENTS.md](AGENTS.md) and [CHANGELOG.md](CHANGELOG.md) for source
validation and release rules. Claude Code changes are published only from
`claude-code`, never from `main`.

## License

MIT. See [LICENSE](LICENSE).
