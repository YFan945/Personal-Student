"""Resolve machine-readable visual style tokens for PPTX production and QA."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / "references" / "design-tokens.json"


# These profiles are executable defaults, not prose-only style suggestions.  Keep
# them here so old design-tokens.json files remain readable while callers always
# receive the complete v2 Style DNA contract.
STYLE_VISUAL_PROFILES: dict[str, dict[str, Any]] = {
    "academic-rigorous": {"shape_grammar": ["rect", "bracket"], "corner_svg_set": "academic-bracket", "component_variants": "evidence-rail", "image_frame": "captioned-document", "background_treatment": "baseline-grid", "text_alignment_policy": "structured-left", "visual_rhythm": "measured-proof", "fallback_illustration": "evidence-map"},
    "berry-cream": {"shape_grammar": ["ellipse", "pill"], "corner_svg_set": "berry-petal", "component_variants": "voice-cluster", "image_frame": "soft-portrait", "background_treatment": "cream-bloom", "text_alignment_policy": "warm-balanced", "visual_rhythm": "intimate-pause", "fallback_illustration": "participant-cluster"},
    "charcoal-editorial": {"shape_grammar": ["rect", "parallelogram"], "corner_svg_set": "editorial-crop", "component_variants": "offset-column", "image_frame": "monochrome-crop", "background_treatment": "paper-rule", "text_alignment_policy": "editorial-left", "visual_rhythm": "asymmetric-spread", "fallback_illustration": "editorial-index"},
    "cherry-bold": {"shape_grammar": ["chevron", "parallelogram"], "corner_svg_set": "cherry-slash", "component_variants": "decision-flag", "image_frame": "duotone-cut", "background_treatment": "diagonal-field", "text_alignment_policy": "decisive-center", "visual_rhythm": "compressed-impact", "fallback_illustration": "decision-path"},
    "coral-energy": {"shape_grammar": ["ellipse", "arch"], "corner_svg_set": "coral-arc", "component_variants": "momentum-disc", "image_frame": "bright-orbit", "background_treatment": "rising-path", "text_alignment_policy": "active-balanced", "visual_rhythm": "launch-and-proof", "fallback_illustration": "momentum-route"},
    "creative-student": {"shape_grammar": ["parallelogram", "pill"], "corner_svg_set": "studio-tape", "component_variants": "sticky-collage", "image_frame": "taped-polaroid", "background_treatment": "paper-scrap", "text_alignment_policy": "studio-mixed", "visual_rhythm": "iterative-collage", "fallback_illustration": "prototype-wall"},
    "data-driven": {"shape_grammar": ["rect", "bracket"], "corner_svg_set": "data-axis", "component_variants": "plot-frame", "image_frame": "neutral-evidence", "background_treatment": "coordinate-grid", "text_alignment_policy": "analytical-left", "visual_rhythm": "metric-interval", "fallback_illustration": "data-relationship"},
    "forest-moss": {"shape_grammar": ["ellipse", "arch"], "corner_svg_set": "moss-contour", "component_variants": "terrain-layer", "image_frame": "organic-window", "background_treatment": "topographic-wash", "text_alignment_policy": "grounded-left", "visual_rhythm": "layered-landscape", "fallback_illustration": "place-system"},
    "midnight-business": {"shape_grammar": ["parallelogram", "chevron"], "corner_svg_set": "midnight-beam", "component_variants": "luminous-stack", "image_frame": "navy-overlay", "background_treatment": "deep-beam", "text_alignment_policy": "executive-grid", "visual_rhythm": "anchor-and-brief", "fallback_illustration": "decision-stack"},
    "modern-minimal": {"shape_grammar": ["none", "ellipse"], "corner_svg_set": "minimal-focus", "component_variants": "open-plane", "image_frame": "quiet-crop", "background_treatment": "open-canvas", "text_alignment_policy": "focal-balance", "visual_rhythm": "whitespace-pulse", "fallback_illustration": "single-focus"},
    "ocean-tech": {"shape_grammar": ["hexagon", "ellipse"], "corner_svg_set": "ocean-circuit", "component_variants": "node-network", "image_frame": "technical-viewport", "background_treatment": "signal-field", "text_alignment_policy": "system-grid", "visual_rhythm": "overview-and-zoom", "fallback_illustration": "system-network"},
    "sage-calm": {"shape_grammar": ["ellipse", "pill"], "corner_svg_set": "sage-orbit", "component_variants": "reflection-loop", "image_frame": "soft-window", "background_treatment": "quiet-orbit", "text_alignment_policy": "calm-balance", "visual_rhythm": "gentle-progression", "fallback_illustration": "reflection-cycle"},
    "teal-trust": {"shape_grammar": ["pill", "hexagon"], "corner_svg_set": "teal-checkpoint", "component_variants": "service-lane", "image_frame": "context-window", "background_treatment": "handoff-route", "text_alignment_policy": "service-grid", "visual_rhythm": "need-to-handoff", "fallback_illustration": "service-journey"},
    "warm-terracotta": {"shape_grammar": ["arch", "parallelogram"], "corner_svg_set": "terracotta-stamp", "component_variants": "archive-layer", "image_frame": "archival-arch", "background_treatment": "material-wash", "text_alignment_policy": "narrative-left", "visual_rhythm": "chronology-pause", "fallback_illustration": "archive-timeline"},
}


def style_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def resolve_design_tokens(visual_style: str | None) -> dict[str, Any]:
    """Return resolved defaults plus a named style; reject unknown named styles."""
    catalog = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    styles = catalog["styles"]
    key = style_key(visual_style or "modern-minimal")
    if key not in styles:
        tokens = copy.deepcopy(catalog["defaults"])
        tokens["style_key"] = key or "custom"
        tokens["style_name"] = visual_style or "Custom"
        tokens["custom_style"] = True
        return tokens
    tokens = copy.deepcopy(catalog["defaults"])
    _merge(tokens, styles[key])
    tokens.setdefault("style_dna", {})
    _merge(tokens["style_dna"], STYLE_VISUAL_PROFILES[key])
    tokens["style_key"] = key
    tokens["style_name"] = styles[key]["name"]
    return tokens
