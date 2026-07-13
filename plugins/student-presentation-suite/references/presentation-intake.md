# Presentation Intake

This is the canonical intake contract for student presentation work. Reuse facts
already supplied by the user, attached materials, an existing deck, or Slide
Spec meta. Never ask for a confirmed item again.

## Intake Modes

- PPTX creation or existing-deck editing: full intake is a hard gate.
- Outline-only planning: ask only for missing items that materially change the
  story, timing, evidence, or ownership; low-risk preferences may be stated as
  assumptions.
- Review-only work: proceed when the artifact is readable; ask only for missing
  duration, presentation type, group format, or rubric when it materially
  changes the review.

Use `presentation-brief.md` for scenario classification, audience depth,
interaction mode, quality level, structure mode, and generation controls.
`beginner` mode explains recommendations; `expert` mode asks only unresolved
high-impact decisions. Both modes keep the full PPTX confirmation gate.

## Full PPTX Intake

Confirm every item before production:

| Item | Recommended value when missing | Why it matters |
| --- | --- | --- |
| Topic | Restate the user's topic as one focused sentence | Defines the story and slide claims |
| Course/context | General undergraduate classroom report | Controls terminology and academic framing |
| Presentation type | Coursework report | Determines required sections |
| Audience | Teacher and classmates | Controls explanation depth |
| Scenario | Coursework | Selects scoring and story defaults |
| Audience depth | Standard | Controls terminology and explanation |
| Language | Follow the user's language | Controls slide and note language |
| Duration | 5 minutes | Controls scope and timing |
| Slide count | 7-9 slides for 5 minutes | Controls density |
| Format | Individual unless members are named | Controls ownership and handoffs |
| Rubric/required sections | No supplied rubric; use standard academic structure | Controls scoring priorities |
| Source material | User material plus stable general background | Controls evidence boundaries |
| Template/branding | No required template, logo, or brand | Controls layout constraints |
| Image strategy | Diagram-only or generated abstract visuals; no web images | Controls sourcing and production |
| Visual style | Recommend three topic-fit styles; choose one only after confirmation | Controls visual direction |
| Deliverables | PPTX, speaker notes, preview/contact sheet; add change summary for edits | Controls completion criteria |
| Interaction/quality mode | Beginner + high-score | Controls guidance, evidence, and rehearsal depth |
| Structure mode | Scenario default | Controls the narrative spine |
| Content controls | 40 English words / 80 Chinese characters, balanced visual/text, notes on | Controls density and output layers |
| Citation/export/versioning | Classroom citations; requested local exports; versioning on for edits | Controls traceability and rollback |

If duration is known but slide count is not, recommend:

- 3 minutes: 5-7 slides
- 5 minutes: 7-9 slides
- 8 minutes: 9-12 slides
- 10 minutes: 10-14 slides
- 15 minutes: 14-18 slides

## Required Interaction

For an incomplete PPTX request, use `AskUserQuestion` to let the user select
each unresolved field directly — one question per field, with recommended values
as the first option. Do NOT list all fields in text and ask for a consolidated
reply.

### Interaction flow

1. Extract all already-confirmed facts from the user's request; display them as
   `✅ 已确认` in a short summary.
2. Identify unresolved fields that have clear option sets. Batch them into
   `AskUserQuestion` calls (max 4 questions per call, 2-4 options each).
3. For each question, the first option is always the recommended value, labeled
   with `（推荐）`. Include a one-line impact statement in each option's
   `description`.
4. After the user selects, move to the next batch of unresolved fields. Repeat
   until all fields are resolved.
5. If the user types “你决定”, “按推荐来”, or “use the recommendations” at any
   point, stop asking and fill all remaining fields with recommended values.
6. After all fields are resolved, show the complete `Production Summary` and ask
   for final confirmation. Delegation does NOT itself move the state to
   `intake_confirmed`; approval of the summary does.
7. Do not run environment checks, generation scripts, rendering, or delivery
   checks while the state is `intake_pending`.
8. If a field has no natural option set (e.g. Topic, Course/context, Rubric),
   use `AskUserQuestion` with `”Other”` as a free-text fallback, or ask inline.

### Question batches (by priority)

Batch fields so that the most impactful decisions come first. Typical grouping:

**Round 1 — 场景与受众** (pick the ones that are unresolved):
- `Presentation type` → options: Coursework report, Defense/答辩, Competition/竞赛, Club showcase, Research paper
- `Scenario` → options from scenario classification table
- `Audience` → options: Teacher + classmates, Non-specialists, Judges/Panel, Mixed
- `Audience depth` → options: Introductory, Standard, Expert

**Round 2 — 规模与格式**:
- `Duration` → options: 3min (5-7页), 5min (7-9页), 8min (9-12页), 10min (10-14页), 15min (14-18页)
- `Format` → options: Individual/个人, Group/小组 (2-4人), Group/小组 (5+人)
- `Quality level` → options: Basic, High-score/高分
- `Interaction mode` → options: Beginner/新手引导, Expert/专家模式

**Round 3 — 视觉与素材**:
- `Visual style` → **两步选择**（样式 > 4 种时强制分步）:
  - **Step A — 风格方向**：从 `visual-style-menu.md` 按场景归类为 4 个方向，让用户先选方向
    → 学术严谨类 / 商务专业类 / 科技现代类 / 创意人文类
    （每个方向下列出包含的样式名和中文别名，让用户知道里面有什么）
  - **Step B — 具体样式**：根据用户选的方向，展示该方向下的 3-4 个具体样式，标注最佳推荐
    → 如果某方向超过 4 个样式，拆成 2 轮
  - **快捷出口**：Step A 的选项之一始终是 "显示全部 14 种样式"，选此则分 4 轮逐一展示所有样式
  - **风格方向归类参考**（从 `visual-style-menu.md` 来）:
    - 学术严谨类：Academic Rigorous、Data Driven、Charcoal Editorial
    - 商务专业类：Midnight Business、Teal Trust、Modern Minimal
    - 科技现代类：Ocean Tech、Modern Minimal、Data Driven
    - 创意人文类：Creative Student、Coral Energy、Forest Moss、Warm Terracotta、Berry Cream、Sage Calm、Cherry Bold
  - Step A 必须根据 topic 推荐最匹配的方向作为第一个选项 `（推荐）`，而不是机械按固定顺序
- `Image strategy` → options: Diagram-only/仅图表, Generated abstract/生成抽象图, Photo/照片, No images/无图
- `Citation style` → options: Classroom/课堂引用, APA, IEEE, MLA, None
- 如果本轮的 3 个问题填不满 4 个槽位（视觉风格已占 2 轮），把 Citation style 挪到 Round 2 或 Round 4

**Round 4 — 输出格式**:
- `Deliverables` (multi-select) → options: PPTX, Speaker notes/讲稿, Preview image/预览, PDF export, Contact sheet
- Other output-specific fields as needed

### Example

```
已确认：Topic=深度学习入门, Language=中文, Source material=课程讲义

→ 调用 AskUserQuestion（Round 1，4 个问题）让用户选择：
  1. Presentation type → Coursework report（推荐）
  2. Scenario → coursework
  3. Audience → Teacher + classmates（推荐）
  4. Audience depth → Standard（推荐）

→ 用户选择后，调用 AskUserQuestion（Round 2）：
  1. Duration → 5min（推荐）
  2. Format → Individual（推荐）
  3. Quality level → High-score（推荐）
  4. Interaction mode → Beginner（推荐）

→ 用户选择后，调用 AskUserQuestion（Round 3a — 风格方向）：
  1. 风格方向 → 科技现代类（推荐）/ 学术严谨类 / 商务专业类 / 创意人文类

→ 用户选"科技现代类"后，调用 AskUserQuestion（Round 3b — 具体样式）：
  1. Visual style → Ocean Tech 海洋科技（推荐）/ Modern Minimal 现代简洁 / Data Driven 数据驱动
  2. Image strategy → Diagram-only（推荐）
  3. Citation style → Classroom（推荐）

→ 所有字段确认完毕，展示完整 Production Summary 等待最终确认
```

### Delegation shortcut

If the user says “你决定”, “按推荐来”, or “use the recommendations” at any
point, fill every remaining unresolved field with the recommended value. Then
show the complete `Production Summary` and ask for explicit confirmation.

If all fields were already supplied in the initial request, skip the question
rounds and go directly to showing the complete `Production Summary` for
confirmation.

## Production Summary

The confirmation summary must list all full-intake fields plus the planned output
directory or filename prefix when known. Only an affirmative reply to this
summary moves the workflow to `intake_confirmed`.

After confirmation, map supported values into Slide Spec `meta`:

- `topic`, `presentation_type`, `audience`, `language`, `duration_min`, `slide_count`
- `scenario`, `audience_type`, `audience_depth`, `structure_mode`
- `interaction_mode`, `quality_level`, `max_words_per_slide`,
  `max_chinese_chars_per_slide`, `visual_text_ratio`
- `include_speaker_notes`, `include_key_lines`, `citation_style`,
  `export_formats`, `versioning`
- `format`, `members`, `course`, `rubric`
- `source_material`, `template`, `logo`, `image_source`, `visual_style`
- `deliverables`, `output_prefix`

Use existing-deck top-level fields for editing: `source_deck`, `edit_intent`,
`review_findings`, `preserve`, and `change_summary_required`.

For complex or file-producing work, save the confirmed global controls as a
Presentation Brief and validate it before creating the Slide Spec. Do not ask
the user to approve both documents separately when the Slide Spec faithfully
implements the already approved summary.

## Workflow States

`intake_pending → intake_confirmed → planned → producing → qa → complete`

- `intake_pending`: full intake is incomplete or its summary is unconfirmed.
- `intake_confirmed`: user approved the complete Production Summary.
- `planned`: slide spine or Slide Spec is ready.
- `producing`: editable files are being generated or edited.
- `qa`: static checks, rendering, inspection, and correction are running.
- `complete`: all required deliverables and gates passed.
- `incomplete`: a usable artifact exists but a required deliverable or QA gate failed.
- `blocked`: production cannot proceed because a required input, artifact, or runtime dependency is unavailable.

Never claim production has started before `intake_confirmed`. `incomplete` and
`blocked` may be entered from any later state when their conditions are met.

For PPTX work, persist this state under the active project with
`scripts/workflow_guard.py`. The plugin PreToolUse hook denies suite production
commands when no confirmed state exists. The summary file hash is retained as
the auditable confirmation boundary.
