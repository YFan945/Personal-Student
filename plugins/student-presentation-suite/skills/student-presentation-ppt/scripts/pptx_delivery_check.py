#!/usr/bin/env python3
"""Check expected PPTX delivery files for student presentation generation.

This script verifies file existence, counts slides from PPTX XML, and can include
static XML risk findings from the review checker. It does not render slides, so
preview/contact-sheet review is still required for visual QA.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check PPTX delivery package")
    parser.add_argument("--pptx", type=Path, required=True, help="Generated PPTX path")
    parser.add_argument("--notes", type=Path, help="Speaker notes Markdown path")
    parser.add_argument(
        "--preview",
        type=Path,
        action="append",
        default=[],
        help="Preview image, contact sheet, or exported PDF path; repeatable",
    )
    parser.add_argument("--pdf", type=Path, help="Optional requested PDF export")
    parser.add_argument("--teleprompter", type=Path, help="Optional requested HTML teleprompter")
    parser.add_argument("--quality-report", type=Path, help="Optional requested JSON quality report")
    parser.add_argument("--style-report", type=Path, help="Optional style-adherence JSON report")
    parser.add_argument("--revision-manifest", type=Path, help="Optional requested revision manifest")
    parser.add_argument("--qa-manifest", type=Path, help="Rendered QA evidence manifest JSON path")
    parser.add_argument("--output", type=Path, help="Optional delivery-report.json output path")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--allow-missing-notes",
        action="store_true",
        help="Do not require a notes file; use only when notes are embedded or explicitly out of scope",
    )
    parser.add_argument(
        "--allow-missing-preview",
        action="store_true",
        help="Do not require a preview/contact sheet; visual QA must then be reported as incomplete",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero unless all file, static-risk, preview, and QA-manifest gates pass",
    )
    return parser.parse_args()


def slide_number(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def count_slides(path: Path) -> tuple[int | None, str | None]:
    try:
        with zipfile.ZipFile(path) as zf:
            slide_names = [
                n
                for n in zf.namelist()
                if n.startswith("ppt/slides/slide") and n.endswith(".xml")
            ]
            return len(sorted(slide_names, key=slide_number)), None
    except (FileNotFoundError, PermissionError, OSError, zipfile.BadZipFile, KeyError) as exc:
        return None, str(exc)



def _load_inspect_pptx():
    from shared._import_helpers import load_inspect_pptx  # noqa: PLC0415
    return load_inspect_pptx(__file__)


def file_info(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        exists = path.is_file()
        size = path.stat().st_size if exists else None
        error = None
    except (PermissionError, OSError) as exc:
        exists = False
        size = None
        error = str(exc)
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": size,
        "error": error,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_preview(path: Path) -> dict[str, Any]:
    """Decode raster previews and reject tiny or single-colour placeholders."""
    result: dict[str, Any] = {"path": str(path.resolve()), "valid": False, "error": None}
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        result["error"] = "Preview must be a PNG or JPEG raster image."
        return result
    try:
        from PIL import Image, ImageStat  # noqa: PLC0415

        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            extrema = ImageStat.Stat(image.convert("RGB")).extrema
        result.update({"width": width, "height": height, "sha256": sha256_file(path)})
        if width < 320 or height < 180:
            result["error"] = "Preview dimensions are too small for visual inspection."
        elif all(low == high for low, high in extrema):
            result["error"] = "Preview is a single-colour placeholder, not rendered evidence."
        else:
            result["valid"] = True
    except (ImportError, OSError, ValueError) as exc:
        result["error"] = str(exc)
    return result


def validate_qa_manifest(
    manifest_path: Path | None,
    pptx: Path,
    slide_count: int | None,
    preview_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate evidence that the current PPTX was rendered and visually reviewed."""
    result: dict[str, Any] = {"provided": manifest_path is not None, "valid": False, "errors": []}
    if manifest_path is None:
        result["errors"].append("QA manifest is required.")
        return result
    result["path"] = str(manifest_path)
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Manifest root must be an object.")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result["errors"].append(f"Cannot read QA manifest: {exc}")
        return result
    result["manifest"] = data
    if not pptx.is_file() or data.get("pptx_sha256") != sha256_file(pptx):
        result["errors"].append("pptx_sha256 does not match the current PPTX.")
    if slide_count is None or data.get("slide_count") != slide_count:
        result["errors"].append("slide_count does not match the PPTX.")
    if slide_count is None or data.get("rendered_page_count") != slide_count:
        result["errors"].append("rendered_page_count must equal PPTX slide_count.")
    if data.get("scenario_contract_passed") is not True:
        result["errors"].append("scenario_contract_passed must be true.")
    inspection = data.get("visual_inspection")
    if not isinstance(inspection, dict) or inspection.get("completed") is not True:
        result["errors"].append("visual_inspection.completed must be true.")
    else:
        expected_pages = list(range(1, (slide_count or 0) + 1))
        if sorted(inspection.get("inspected_pages") or []) != expected_pages:
            result["errors"].append("visual_inspection.inspected_pages must cover every slide.")
        if inspection.get("remaining_blockers") != 0:
            result["errors"].append("visual_inspection.remaining_blockers must be 0.")
        cycles = inspection.get("repair_cycles")
        if not isinstance(cycles, int) or cycles < 1:
            if not isinstance(inspection.get("no_repair_needed_reason"), str) or not inspection["no_repair_needed_reason"].strip():
                result["errors"].append("Record repair_cycles >= 1 or a no_repair_needed_reason.")
    listed_files = data.get("preview_files")
    listed_hashes = data.get("preview_sha256")
    if not isinstance(listed_files, list) or not listed_files:
        result["errors"].append("preview_files must list rendered preview evidence.")
    elif not isinstance(listed_hashes, list) or len(listed_hashes) != len(listed_files):
        result["errors"].append("preview_sha256 must correspond to preview_files.")
    else:
        actual = {item.get("path"): item for item in preview_checks}
        for listed, expected_hash in zip(listed_files, listed_hashes):
            resolved = str((manifest_path.parent / listed).resolve()) if not Path(listed).is_absolute() else str(Path(listed).resolve())
            check = actual.get(resolved)
            if not check or not check.get("valid") or check.get("sha256") != expected_hash:
                result["errors"].append(f"Preview evidence is invalid or stale: {listed}")
    result["valid"] = not result["errors"]
    return result


def validate_style_report(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"provided": False, "valid": None, "errors": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"provided": True, "valid": False, "errors": [f"Cannot read style report: {exc}"]}
    if not isinstance(data, dict) or data.get("ok") is not True:
        return {"provided": True, "valid": False, "errors": ["Style report does not pass."], "report": data}
    return {"provided": True, "valid": True, "errors": [], "report": data}


def expected_notes_path(pptx: Path) -> Path:
    stem = pptx.stem
    prefix = stem[: -len("-presentation")] if stem.endswith("-presentation") else stem
    return pptx.with_name(f"{prefix}-speaker-notes.md")


def expected_preview_paths(pptx: Path) -> list[Path]:
    stem = pptx.stem
    prefix = stem[: -len("-presentation")] if stem.endswith("-presentation") else stem
    parent = pptx.parent
    discovered = sorted(
        {
            *parent.glob(f"{prefix}*preview*.png"),
            *parent.glob(f"{prefix}*contact*.png"),
            *parent.glob(f"{prefix}*preview*.pdf"),
            *parent.glob(f"{prefix}*contact*.pdf"),
        }
    )
    return discovered or [parent / f"{prefix}-preview.png"]



def summarize_static_risks(static_result: dict[str, Any]) -> dict[str, Any]:
    findings = static_result.get("findings", []) if isinstance(static_result, dict) else []
    risk_counter: Counter[str] = Counter()
    acceptable_minor_counter: Counter[str] = Counter()
    blocker_like: list[dict[str, Any]] = []
    minor_markers = (
        "footer",
        "page",
        "slide",
        "source",
        "caption",
        "kicker",
        "eyebrow",
        "页码",
        "来源",
        "注释",
    )
    blocker_risks = {
        "high-text-density-overflow-risk",
        "text-vertical-overflow-risk",
        "paragraph-heavy-slide-text",
        "heading-font-size-below-24pt",
        "shape-outside-slide",
        "low-whitespace-risk",
        "unexpected-object-overlap-risk",
        "low-resolution-image-risk",
        "image-aspect-distortion-risk",
        "title-outside-title-zone",
        "footer-zone-invasion",
        "insufficient-gutter-risk",
        "low-foreground-background-contrast",
        "connector-crosses-object-risk",
        "chart-missing-title-risk",
        "chart-label-font-size-below-18pt",
        "text-box-padding-below-16pt",
        "alignment-tolerance-risk",
    }
    for item in findings:
        risks = item.get("risk", []) or []
        text_preview = str(item.get("text_preview", ""))
        lower_preview = text_preview.lower()
        min_font = item.get("min_font_pt")
        char_count = item.get("char_count") or 0
        looks_minor = (
            char_count <= 24
            and min_font is not None
            and min_font >= 10
            and any(marker in lower_preview or marker in text_preview for marker in minor_markers)
        )
        for risk in risks:
            risk_counter[risk] += 1
            if looks_minor and risk in {"font-size-below-20pt", "chinese-font-size-below-22pt", "small-text-box-risk"}:
                acceptable_minor_counter[risk] += 1
        if any(risk in blocker_risks for risk in risks) and not looks_minor:
            blocker_like.append(
                {
                    "slide": item.get("slide"),
                    "shape": item.get("shape"),
                    "text_preview": text_preview[:80],
                    "risk": risks,
                    "min_font_pt": min_font,
                }
            )
    return {
        "risk_breakdown": dict(sorted(risk_counter.items())),
        "acceptable_minor_risk_breakdown": dict(sorted(acceptable_minor_counter.items())),
        "blocker_like_count": len(blocker_like),
        "blocker_like_examples": blocker_like[:10],
    }


def inspect_delivery(
    pptx: Path,
    notes: Path | None,
    previews: list[Path],
    *,
    require_notes: bool = True,
    require_preview: bool = True,
    extra_files: dict[str, Path | None] | None = None,
    qa_manifest: Path | None = None,
    style_report: Path | None = None,
) -> dict[str, Any]:
    if require_notes and notes is None:
        notes = expected_notes_path(pptx)
    if require_preview and not previews:
        previews = expected_preview_paths(pptx)
    pptx_info = file_info(pptx)
    slide_count, slide_error = count_slides(pptx)
    preview_infos = [file_info(path) for path in previews]
    preview_checks = [inspect_preview(path) for path in previews if path.is_file()]
    missing = []
    if not pptx_info or not pptx_info["exists"]:
        missing.append("pptx")
    if require_notes and (notes is None or not notes.is_file()):
        missing.append("notes")
    if require_preview and not any(info and info["exists"] for info in preview_infos):
        missing.append("preview")
    extra_infos = {
        name: file_info(path)
        for name, path in (extra_files or {}).items()
        if path is not None
    }
    for name, info in extra_infos.items():
        if not info or not info["exists"]:
            missing.append(name)

    static_summary: dict[str, Any] = {
        "available": False,
        "finding_count": None,
        "error": None,
    }
    if pptx_info and pptx_info["exists"]:
        static_result = _load_inspect_pptx()(pptx)
        static_summary = {
            "available": True,
            "finding_count": len(static_result.get("findings", [])),
            "error": static_result.get("error"),
            "note": static_result.get("note"),
            "font_families": static_result.get("font_families", []),
            **summarize_static_risks(static_result),
        }

    qa_summary = validate_qa_manifest(qa_manifest, pptx, slide_count, preview_checks)
    style_summary = validate_style_report(style_report)
    required_files_valid = not missing
    pptx_readable = pptx_info is not None and pptx_info["exists"] and slide_error is None
    render_qa_valid = bool(preview_checks) and all(item["valid"] for item in preview_checks)
    ok = bool(
        required_files_valid
        and pptx_readable
        and slide_count and slide_count > 0
        and static_summary.get("error") is None
        and static_summary.get("blocker_like_count", 0) == 0
        and render_qa_valid
        and qa_summary["valid"]
        and style_summary["valid"] is not False
    )

    inspection = qa_summary.get("manifest", {}).get("visual_inspection", {}) if qa_summary.get("valid") else {}
    delivery_report = {
        "ok": ok,
        "status": "complete" if ok else "incomplete",
        "slide_count": slide_count,
        "static_blockers": static_summary.get("blocker_like_count"),
        "render_blockers": len(qa_summary.get("errors", [])),
        "scenario_contract_passed": qa_summary.get("manifest", {}).get("scenario_contract_passed") if qa_summary.get("valid") else False,
        "style_adherence_passed": style_summary.get("valid"),
        "preview_page_coverage": f"{len(inspection.get('inspected_pages', []))}/{slide_count or 0}",
        "repair_cycles": inspection.get("repair_cycles"),
    }
    return {
        "pptx": pptx_info,
        "notes": file_info(notes),
        "previews": preview_infos,
        "preview_validation": preview_checks,
        "extra_files": extra_infos,
        "slide_count": slide_count,
        "slide_count_error": slide_error,
        "static_xml_risk_summary": static_summary,
        "qa_manifest": qa_summary,
        "style_adherence": style_summary,
        "missing_expected_files": missing,
        "ok": ok,
        "delivery_report": delivery_report,
        "requirements": {
            "notes_required": require_notes,
            "preview_required": require_preview,
        },
        "note": (
            "Strict delivery requires readable rendered previews and a QA manifest bound to the current PPTX."
        ),
    }


def print_text(result: dict[str, Any]) -> None:
    pptx = result["pptx"]
    print(result["note"])
    print(f"PPTX: {pptx['path']} exists={pptx['exists']} size={pptx['size_bytes']}")
    notes = result.get("notes")
    if notes is not None:
        print(f"Notes: {notes['path']} exists={notes['exists']} size={notes['size_bytes']}")
    for idx, preview in enumerate(result.get("previews", []), start=1):
        print(
            f"Preview {idx}: {preview['path']} exists={preview['exists']} "
            f"size={preview['size_bytes']}"
        )
    for idx, preview in enumerate(result.get("preview_validation", []), start=1):
        print(f"Preview QA {idx}: valid={preview['valid']} error={preview['error']}")
    for name, info in result.get("extra_files", {}).items():
        print(f"{name}: {info['path']} exists={info['exists']} size={info['size_bytes']}")
    print(f"Slide count: {result['slide_count']}")
    if result["slide_count_error"]:
        print(f"Slide count error: {result['slide_count_error']}")
    static = result["static_xml_risk_summary"]
    print(
        "Static XML risks: "
        f"available={static['available']} count={static['finding_count']} error={static['error']}"
    )
    if static.get("risk_breakdown"):
        print("Risk breakdown: " + json.dumps(static["risk_breakdown"], ensure_ascii=False, sort_keys=True))
    if static.get("acceptable_minor_risk_breakdown"):
        print(
            "Acceptable minor risk breakdown: "
            + json.dumps(static["acceptable_minor_risk_breakdown"], ensure_ascii=False, sort_keys=True)
        )
    if static.get("blocker_like_count") is not None:
        print(f"Blocker-like static risks: {static['blocker_like_count']}")
    if result["missing_expected_files"]:
        print("Missing expected files: " + ", ".join(result["missing_expected_files"]))
    print(f"Delivery OK: {result['ok']}")


def main() -> None:
    args = parse_args()
    result = inspect_delivery(
        args.pptx,
        args.notes,
        args.preview,
        require_notes=not args.allow_missing_notes,
        require_preview=not args.allow_missing_preview,
        extra_files={
            "pdf": args.pdf,
            "teleprompter": args.teleprompter,
            "quality-report": args.quality_report,
            "style-report": args.style_report,
            "revision-manifest": args.revision_manifest,
        },
        qa_manifest=args.qa_manifest,
        style_report=args.style_report,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result["delivery_report"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.strict and not result["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
