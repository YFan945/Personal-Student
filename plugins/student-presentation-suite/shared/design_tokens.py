"""Resolve machine-readable visual style tokens for PPTX production and QA."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / "references" / "design-tokens.json"


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
    tokens["style_key"] = key
    tokens["style_name"] = styles[key]["name"]
    return tokens
