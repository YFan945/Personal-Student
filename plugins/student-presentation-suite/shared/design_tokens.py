"""Resolve lightweight visual references for PPTX production and QA."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from shared.pptx_static_core import contrast_ratio

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / "references" / "design-tokens.json"

STYLE_ALIASES = {
    "berry-cream": "warm-terracotta",
    "sage-calm": "forest-moss",
}

PALETTE_ROLES = (
    "canvas",
    "surface",
    "primary_text",
    "secondary_text",
    "primary_accent",
    "secondary_accent",
)
BACKGROUND_ROLES = ("cover", "content", "section", "closing")
HEX_COLOR = re.compile(r"^[0-9A-Fa-f]{6}$")


def style_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def validate_custom_style(custom: dict[str, Any] | None) -> list[str]:
    """Return actionable validation errors for the four-field Other contract."""
    if not isinstance(custom, dict):
        return ["visual_style_custom is required when visual_style is Other"]
    errors: list[str] = []
    expected = {"style_character", "palette", "backgrounds", "svg_reference"}
    extra = sorted(set(custom) - expected)
    if extra:
        errors.append(f"visual_style_custom contains unsupported fields: {', '.join(extra)}")
    if not isinstance(custom.get("style_character"), str) or not custom["style_character"].strip():
        errors.append("visual_style_custom.style_character is required")
    palette = custom.get("palette")
    if not isinstance(palette, dict):
        errors.append("visual_style_custom.palette is required")
    else:
        extra_palette = sorted(set(palette) - set(PALETTE_ROLES))
        if extra_palette:
            errors.append(
                "visual_style_custom.palette contains unsupported roles: "
                + ", ".join(extra_palette)
            )
        for role in PALETTE_ROLES:
            value = str(palette.get(role, ""))
            if not HEX_COLOR.fullmatch(value):
                errors.append(f"visual_style_custom.palette.{role} must be a 6-digit hex color")
        if not errors:
            for text_role in ("primary_text", "secondary_text"):
                for background_role in ("canvas", "surface"):
                    ratio = contrast_ratio(palette[text_role], palette[background_role])
                    if ratio < 4.5:
                        errors.append(
                            f"visual_style_custom.palette.{text_role} must reach 4.5:1 "
                            f"against {background_role}; got {ratio:.2f}:1"
                        )
            for background_role in ("canvas", "surface"):
                ratio = contrast_ratio(palette["primary_accent"], palette[background_role])
                if ratio < 3.0:
                    errors.append(
                        "visual_style_custom.palette.primary_accent must reach 3:1 "
                        f"against {background_role}; got {ratio:.2f}:1"
                    )
    backgrounds = custom.get("backgrounds")
    if not isinstance(backgrounds, dict):
        errors.append("visual_style_custom.backgrounds is required")
    else:
        extra_backgrounds = sorted(set(backgrounds) - set(BACKGROUND_ROLES))
        if extra_backgrounds:
            errors.append(
                "visual_style_custom.backgrounds contains unsupported roles: "
                + ", ".join(extra_backgrounds)
            )
        for role in BACKGROUND_ROLES:
            if not isinstance(backgrounds.get(role), str) or not backgrounds[role].strip():
                errors.append(f"visual_style_custom.backgrounds.{role} is required")
    svg_reference = custom.get("svg_reference")
    if not isinstance(svg_reference, dict):
        errors.append("visual_style_custom.svg_reference is required")
    else:
        extra_svg = sorted(set(svg_reference) - {"name", "usage"})
        if extra_svg:
            errors.append(
                "visual_style_custom.svg_reference contains unsupported fields: "
                + ", ".join(extra_svg)
            )
        for role in ("name", "usage"):
            if not isinstance(svg_reference.get(role), str) or not svg_reference[role].strip():
                errors.append(f"visual_style_custom.svg_reference.{role} is required")
    return errors


def resolve_design_tokens(
    visual_style: str | None,
    visual_style_custom: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve global safety tokens plus a lightweight visual reference."""
    catalog = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    styles = catalog["styles"]
    requested_name = visual_style or "Modern Minimal"
    requested_key = style_key(requested_name)
    warnings: list[str] = []

    if requested_key in STYLE_ALIASES:
        target = STYLE_ALIASES[requested_key]
        warnings.append(
            f"Legacy visual style {requested_name!r} maps to {styles[target]['name']!r}."
        )
        requested_key = target

    tokens = copy.deepcopy(catalog["defaults"])
    if requested_key == "other":
        errors = validate_custom_style(visual_style_custom)
        if errors:
            raise ValueError("; ".join(errors))
        assert visual_style_custom is not None
        _merge(tokens, visual_style_custom)
        tokens["style_key"] = "other"
        tokens["style_name"] = "Other"
        tokens["custom_style"] = True
    elif requested_key in styles:
        _merge(tokens, styles[requested_key])
        tokens["style_key"] = requested_key
        tokens["style_name"] = styles[requested_key]["name"]
    else:
        fallback = styles["modern-minimal"]
        _merge(tokens, fallback)
        tokens["style_character"] = requested_name
        tokens["style_key"] = requested_key or "custom"
        tokens["style_name"] = requested_name or "Custom"
        tokens["custom_style"] = True
        warnings.append(
            "Legacy custom style has no visual_style_custom record; Modern Minimal safety "
            "colors, backgrounds, and SVG reference were used."
        )

    if warnings:
        tokens["compatibility_warnings"] = warnings
    return tokens
