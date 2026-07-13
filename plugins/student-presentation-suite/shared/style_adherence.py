"""Static style-adherence evidence for generated PPTX files."""

from __future__ import annotations

import collections
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Any

from shared.design_tokens import resolve_design_tokens
from shared.pptx_static_core import NS, fill_colors, font_families, slide_number


def _line_widths(root: ET.Element) -> list[float]:
    widths: list[float] = []
    for line in root.findall(".//a:ln", NS):
        try:
            widths.append(round(int(line.attrib.get("w", "0")) / 12700, 2))
        except ValueError:
            continue
    return widths


def _connector_line_widths(root: ET.Element) -> list[float]:
    widths: list[float] = []
    for connector in root.findall(".//p:cxnSp", NS):
        widths.extend(_line_widths(connector))
    return widths


def inspect_style_adherence(pptx: Path, visual_style: str) -> dict[str, Any]:
    tokens = resolve_design_tokens(visual_style)
    palette = set(tokens.get("palette", {}).values())
    colors: collections.Counter[str] = collections.Counter()
    fonts: collections.Counter[str] = collections.Counter()
    lines: collections.Counter[float] = collections.Counter()
    connector_lines: collections.Counter[float] = collections.Counter()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with zipfile.ZipFile(pptx) as archive:
            slides = sorted(
                (name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")),
                key=slide_number,
            )
            for slide in slides:
                root = ET.fromstring(archive.read(slide))
                for color in fill_colors(root):
                    if color.startswith("srgb:"):
                        colors[color.removeprefix("srgb:")] += 1
                fonts.update(font_families(root))
                lines.update(_line_widths(root))
                connector_lines.update(_connector_line_widths(root))
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        return {"ok": False, "error": str(exc), "style": tokens.get("style_name"), "tokens": tokens}

    if tokens.get("custom_style"):
        warnings.append("Custom style uses shared safety tokens; palette adherence cannot be automatically verified.")
    else:
        unexpected = sorted(set(colors) - palette)
        maximum = tokens["style_adherence"]["max_unapproved_srgb_colors"]
        if len(unexpected) > maximum:
            errors.append(f"Found {len(unexpected)} unapproved SRGB colors (limit {maximum}): {', '.join(unexpected)}")
        if colors and tokens["palette"]["primary_accent"] not in colors:
            warnings.append("The configured primary accent was not found in slide XML; verify theme or rendering output.")
    if len(fonts) > tokens["style_adherence"]["max_font_families"]:
        errors.append("Too many explicit font families: " + ", ".join(sorted(fonts)))
    allowed_lines = {
        round(tokens["lines"][key], 2)
        for key in ("hairline_pt", "standard_pt", "emphasis_pt", "section_rule_pt")
    }
    uncommon_lines = sorted(width for width in lines if width and width not in allowed_lines)
    if uncommon_lines:
        warnings.append("Line widths outside the configured system: " + ", ".join(map(str, uncommon_lines)))
    nonconforming_connectors = sorted(width for width in connector_lines if width and width not in allowed_lines)
    if nonconforming_connectors:
        errors.append("Connector widths outside the configured line system: " + ", ".join(map(str, nonconforming_connectors)))
    return {
        "ok": not errors,
        "style": tokens.get("style_name"),
        "tokens": tokens,
        "slide_count": len(slides),
        "observed": {"srgb_colors": dict(colors), "font_families": dict(fonts), "line_widths_pt": dict(lines), "connector_line_widths_pt": dict(connector_lines)},
        "errors": errors,
        "warnings": warnings,
    }
