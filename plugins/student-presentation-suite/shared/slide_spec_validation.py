"""Cross-field validation for Student Presentation Slide Spec data."""

from __future__ import annotations

from typing import Any


SCENARIO_REQUIRED_ROLE_GROUPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "coursework": (("background", "problem"), ("method",), ("evidence", "result"), ("conclusion", "closing")),
    "defense": (("problem",), ("method",), ("result", "evidence"), ("solution", "value"), ("limitation",), ("qa",)),
    "competition": (("problem",), ("solution",), ("method",), ("result", "evidence"), ("value",), ("limitation",)),
    "club-showcase": (("opening", "background"), ("method",), ("result", "evidence"), ("value", "closing")),
    "research": (("problem",), ("background",), ("method",), ("result", "evidence"), ("limitation",), ("conclusion", "closing")),
}


def _validate_scenario_roles(meta: dict[str, Any], slides: list[Any]) -> list[dict[str, str]]:
    scenario = meta.get("scenario")
    required = SCENARIO_REQUIRED_ROLE_GROUPS.get(scenario)
    if not required:
        return []
    roles = [slide.get("role") for slide in slides if isinstance(slide, dict) and slide.get("role")]
    errors: list[dict[str, str]] = []
    if not roles:
        return [{"path": ".slides", "message": f"scenario={scenario} requires story roles on slides"}]
    for alternatives in required:
        if not any(role in alternatives for role in roles):
            errors.append({
                "path": ".slides",
                "message": f"scenario={scenario} requires one of story roles: {', '.join(alternatives)}",
            })
    # Core narrative roles must not appear after the conclusion/closing unless this is Q&A.
    final_indices = [index for index, slide in enumerate(slides) if isinstance(slide, dict) and slide.get("role") in {"conclusion", "closing"}]
    if final_indices:
        last_final = min(final_indices)
        late_core = [
            str(slide.get("role"))
            for slide in slides[last_final + 1:]
            if isinstance(slide, dict) and slide.get("role") in {"background", "problem", "method", "evidence", "result", "solution", "value"}
        ]
        if late_core:
            errors.append({"path": ".slides", "message": "core story roles cannot follow conclusion/closing: " + ", ".join(late_core)})
    return errors


def _validate_visual_semantics(meta: dict[str, Any], slides: list[Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    exempt_kinds = {"cover", "section-divider", "quotation", "references", "appendix", "qa", "closing"}
    for index, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        visual = slide.get("visual")
        kind = slide.get("kind", "content")
        if meta.get("visual_text_ratio") == "visual-led" and kind not in exempt_kinds and not isinstance(visual, dict):
            errors.append({"path": f".slides.{index}.visual", "message": "visual-led mode requires a visual on every content slide"})
        if not isinstance(visual, dict):
            continue
        visual_type = str(visual.get("type", "")).casefold()
        details = visual.get("details")
        if visual_type not in {"timeline", "comparison", "process", "chart"}:
            continue
        if not isinstance(details, dict):
            errors.append({"path": f".slides.{index}.visual.details", "message": f"visual type {visual_type} requires structured details"})
            continue
        if visual_type == "timeline" and not isinstance(details.get("stages"), list):
            errors.append({"path": f".slides.{index}.visual.details.stages", "message": "timeline requires an ordered stages list with at least 3 stages"})
        elif visual_type == "timeline" and len(details["stages"]) < 3:
            errors.append({"path": f".slides.{index}.visual.details.stages", "message": "timeline requires at least 3 stages"})
        if visual_type == "comparison":
            if not isinstance(details.get("items"), list) or len(details["items"]) < 2:
                errors.append({"path": f".slides.{index}.visual.details.items", "message": "comparison requires at least 2 items"})
            if not isinstance(details.get("dimensions"), list) or not details["dimensions"]:
                errors.append({"path": f".slides.{index}.visual.details.dimensions", "message": "comparison requires comparison dimensions"})
        if visual_type == "process" and (not isinstance(details.get("steps"), list) or len(details["steps"]) < 2):
            errors.append({"path": f".slides.{index}.visual.details.steps", "message": "process requires at least 2 steps"})
        if visual_type == "chart":
            required = ("measure", "unit", "scope", "source", "takeaway")
            missing = [field for field in required if not details.get(field)]
            if missing:
                errors.append({"path": f".slides.{index}.visual.details", "message": "chart requires: " + ", ".join(missing)})
    return errors


def semantic_errors(data: Any) -> list[dict[str, str]]:
    """Return semantic errors that JSON Schema cannot express clearly."""
    if not isinstance(data, dict):
        return []

    errors: list[dict[str, str]] = []
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    slides = data.get("slides") if isinstance(data.get("slides"), list) else []

    if slides:
        ids = [slide.get("id") for slide in slides if isinstance(slide, dict)]
        expected_ids = list(range(1, len(slides) + 1))
        if ids != expected_ids:
            errors.append(
                {
                    "path": ".slides",
                    "message": f"slide ids must be unique and contiguous from 1; got {ids}",
                }
            )

        target_count = meta.get("slide_count")
        if isinstance(target_count, int) and target_count != len(slides):
            errors.append(
                {
                    "path": ".meta.slide_count",
                    "message": (
                        f"slide_count is {target_count}, but the spec contains {len(slides)} slides"
                    ),
                }
            )

        duration_min = meta.get("duration_min")
        timings = [
            slide.get("timing_sec")
            for slide in slides
            if isinstance(slide, dict) and isinstance(slide.get("timing_sec"), int)
        ]
        if isinstance(duration_min, (int, float)) and len(timings) == len(slides):
            expected_seconds = float(duration_min) * 60
            actual_seconds = sum(timings)
            tolerance = max(60.0, expected_seconds * 0.35)
            if abs(actual_seconds - expected_seconds) > tolerance:
                errors.append(
                    {
                        "path": ".slides",
                        "message": (
                            f"timing_sec totals {actual_seconds}s, which is inconsistent with "
                            f"duration_min={duration_min} ({expected_seconds:g}s)"
                        ),
                    }
                )

    if meta.get("format") == "group":
        members = meta.get("members")
        if not isinstance(members, list) or not members:
            errors.append(
                {
                    "path": ".meta.members",
                    "message": "group format requires a non-empty members list",
                }
            )
        elif slides:
            allowed = set(members)
            for index, slide in enumerate(slides):
                if not isinstance(slide, dict):
                    continue
                owner = slide.get("owner")
                if owner not in allowed:
                    errors.append(
                        {
                            "path": f".slides.{index}.owner",
                            "message": f"owner {owner!r} is not listed in meta.members",
                        }
                    )

    if meta.get("quality_level") == "high-score":
        required_controls = (
            "scenario",
            "audience_type",
            "audience_depth",
            "structure_mode",
        )
        for field in required_controls:
            if not meta.get(field):
                errors.append(
                    {
                        "path": f".meta.{field}",
                        "message": f"high-score mode requires {field}",
                    }
                )

    errors.extend(_validate_scenario_roles(meta, slides))
    errors.extend(_validate_visual_semantics(meta, slides))

    revision_operation = data.get("revision_operation")
    if revision_operation in {"rewrite-slide", "compress", "expand", "add-evidence"}:
        targets = data.get("target_slides")
        if not isinstance(targets, list) or not targets:
            errors.append(
                {
                    "path": ".target_slides",
                    "message": f"{revision_operation} requires at least one target slide",
                }
            )
    if revision_operation == "rewrite-section" and not data.get("target_section"):
        errors.append(
            {
                "path": ".target_section",
                "message": "rewrite-section requires target_section",
            }
        )

    evidence = data.get("evidence_ledger")
    if isinstance(evidence, list):
        evidence_ids = [
            item.get("id")
            for item in evidence
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        duplicates = sorted({item for item in evidence_ids if evidence_ids.count(item) > 1})
        if duplicates:
            errors.append(
                {
                    "path": ".evidence_ledger",
                    "message": "evidence ids must be unique: " + ", ".join(duplicates),
                }
            )
        known = set(evidence_ids)
        for index, slide in enumerate(slides):
            if not isinstance(slide, dict):
                continue
            refs = slide.get("evidence_refs")
            if isinstance(refs, list):
                unknown = sorted({str(ref) for ref in refs if ref not in known})
                if unknown:
                    errors.append(
                        {
                            "path": f".slides.{index}.evidence_refs",
                            "message": "unknown evidence refs: " + ", ".join(unknown),
                        }
                    )
            if slide.get("lock_reason") and not slide.get("locked"):
                errors.append(
                    {
                        "path": f".slides.{index}.lock_reason",
                        "message": "lock_reason requires locked=true",
                    }
                )

    improvement_fields = (
        "edit_intent",
        "review_findings",
        "preserve",
        "change_summary_required",
    )
    present_improvement_fields = [
        field
        for field in improvement_fields
        if data.get(field) not in (None, False, [], "")
    ]
    if present_improvement_fields and not data.get("source_deck"):
        errors.append(
            {
                "path": ".source_deck",
                "message": (
                    "source_deck is required when using existing-deck improvement fields: "
                    + ", ".join(present_improvement_fields)
                ),
            }
        )

    return errors
