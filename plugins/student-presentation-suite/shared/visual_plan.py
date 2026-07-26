"""Compile deterministic, deck-level visual and layout decisions from Slide Spec."""

from __future__ import annotations

from collections import Counter
from typing import Any

LAYOUT_FAMILIES = {
    "hero",
    "visual-dominant",
    "process-path",
    "timeline",
    "comparison",
    "dashboard",
    "architecture",
    "matrix",
    "quote",
    "summary",
    "reference",
}

TYPE_TO_FAMILY = {
    "title-card": "hero",
    "hero": "hero",
    "image": "visual-dominant",
    "photo": "visual-dominant",
    "illustration": "visual-dominant",
    "annotated-image": "visual-dominant",
    "process": "process-path",
    "flow": "process-path",
    "three-step-process": "process-path",
    "cycle": "process-path",
    "timeline": "timeline",
    "comparison": "comparison",
    "before-after": "comparison",
    "chart": "dashboard",
    "metric": "dashboard",
    "dashboard": "dashboard",
    "architecture": "architecture",
    "system-map": "architecture",
    "swimlane": "architecture",
    "matrix": "matrix",
    "quote": "quote",
    "summary": "summary",
}

ROLE_FAMILIES = {
    "opening": ("hero", "visual-dominant"),
    "background": ("visual-dominant", "timeline"),
    "problem": ("comparison", "visual-dominant"),
    "method": ("process-path", "architecture"),
    "evidence": ("dashboard", "visual-dominant"),
    "result": ("dashboard", "comparison"),
    "solution": ("architecture", "process-path"),
    "value": ("dashboard", "comparison"),
    "limitation": ("comparison", "matrix"),
    "conclusion": ("summary", "hero"),
    "qa": ("hero",),
    "closing": ("hero",),
}

KIND_FAMILIES = {
    "cover": "hero",
    "section-divider": "hero",
    "quotation": "quote",
    "references": "reference",
    "appendix": "reference",
    "qa": "hero",
    "closing": "hero",
}

EXEMPT_KINDS = set(KIND_FAMILIES)


def _normal(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def _choose_family(slide: dict[str, Any], previous: list[str]) -> tuple[str, str]:
    visual = slide.get("visual") if isinstance(slide.get("visual"), dict) else {}
    explicit = _normal(visual.get("layout_family"))
    if explicit in LAYOUT_FAMILIES:
        return explicit, "explicit"
    kind = _normal(slide.get("kind"))
    if kind in KIND_FAMILIES:
        return KIND_FAMILIES[kind], "kind"
    visual_type = _normal(visual.get("type"))
    if visual_type in TYPE_TO_FAMILY:
        return TYPE_TO_FAMILY[visual_type], "visual-type"
    layout = _normal(slide.get("layout"))
    for key, family in TYPE_TO_FAMILY.items():
        if key in layout:
            return family, "layout"
    candidates = ROLE_FAMILIES.get(_normal(slide.get("role")), ("visual-dominant", "comparison"))
    for candidate in candidates:
        if len(previous) < 2 or previous[-2:] != [candidate, candidate]:
            return candidate, "role"
    return candidates[0], "role"


def compile_visual_plan(data: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic visual plan plus pre-generation quality gates."""
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    slides = data.get("slides") if isinstance(data.get("slides"), list) else []
    strict = (
        meta.get("quality_level") == "high-score"
        or meta.get("visual_text_ratio") in {"balanced", "visual-led"}
    )
    plans: list[dict[str, Any]] = []
    families: list[str] = []
    content_families: list[str] = []
    visual_content = 0
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for index, raw_slide in enumerate(slides):
        if not isinstance(raw_slide, dict):
            continue
        family, source = _choose_family(raw_slide, families)
        families.append(family)
        kind = _normal(raw_slide.get("kind") or "content")
        visual = raw_slide.get("visual") if isinstance(raw_slide.get("visual"), dict) else None
        visual_type = _normal(visual.get("type")) if visual else ""
        is_content = kind not in EXEMPT_KINDS
        meaningful = bool(visual and visual_type not in {"", "none", "text", "text-only"})
        if is_content:
            content_families.append(family)
            visual_content += int(meaningful)
            if not meaningful:
                target = f".slides.{index}.visual"
                item = {
                    "path": target,
                    "message": "content slide needs a meaningful editable visual, not a text-only layout",
                }
                (errors if strict else warnings).append(item)
        component = {
            "hero": "addSectionHero",
            "visual-dominant": "addAnnotatedVisual",
            "process-path": "addProcessFlow",
            "timeline": "addTimeline",
            "comparison": "addComparison",
            "dashboard": "addMetricDashboard",
            "architecture": "addArchitecture",
            "matrix": "addMatrix",
            "quote": "addQuotePanel",
            "summary": "addSummary",
            "reference": "addReferenceList",
        }[family]
        if visual_type == "chart":
            component = "addChartWithTakeaway"
        plans.append(
            {
                "slide": raw_slide.get("id", index + 1),
                "role": raw_slide.get("role"),
                "kind": kind,
                "layout_family": family,
                "selection_source": source,
                "visual_type": visual_type or None,
                "component": component,
                "component_payload": {
                    **(visual.get("details") if visual and isinstance(visual.get("details"), dict) else {}),
                    **(
                        {
                            key: visual[key]
                            for key in ("asset", "alt_text", "purpose", "type")
                            if visual and visual.get(key) not in (None, "")
                        }
                    ),
                },
            }
        )

    for index in range(2, len(families)):
        if families[index] == families[index - 1] == families[index - 2]:
            item = {
                "path": f".slides.{index}.visual.layout_family",
                "message": f"layout family {families[index]} repeats more than twice consecutively",
            }
            (errors if strict else warnings).append(item)

    content_count = len(content_families)
    coverage = visual_content / content_count if content_count else 1.0
    required_coverage = 0.7 if strict else 0.5
    if coverage < required_coverage:
        item = {
            "path": ".slides",
            "message": (
                f"meaningful visual coverage is {coverage:.0%}; "
                f"required minimum is {required_coverage:.0%}"
            ),
        }
        (errors if strict else warnings).append(item)
    required_families = min(4, content_count)
    family_count = len(set(content_families))
    if content_count >= 3 and family_count < required_families:
        item = {
            "path": ".slides",
            "message": (
                f"only {family_count} content layout families are used; "
                f"{required_families} are required for deck rhythm"
            ),
        }
        (errors if strict else warnings).append(item)

    longest_run = 0
    current_run = 0
    previous_family: str | None = None
    for family in families:
        current_run = current_run + 1 if family == previous_family else 1
        longest_run = max(longest_run, current_run)
        previous_family = family

    return {
        "ok": not errors,
        "strict": strict,
        "slides": plans,
        "metrics": {
            "slide_count": len(plans),
            "content_slide_count": content_count,
            "meaningful_visual_count": visual_content,
            "meaningful_visual_coverage": round(coverage, 3),
            "layout_family_count": family_count,
            "layout_family_usage": dict(Counter(content_families)),
            "max_consecutive_same_family": longest_run,
        },
        "errors": errors,
        "warnings": warnings,
    }
