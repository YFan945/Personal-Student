#!/usr/bin/env python3
"""Stable PPTX-only command facade for the suite-owned presentation runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.pptx_runtime import (  # noqa: E402
    add_slide,
    clean_package,
    delete_slide,
    pack_directory,
    reorder_slides,
    safe_extract_package,
    validate_pptx,
)
from shared.pptx_runtime.normalize import normalize_generated_package  # noqa: E402
from shared.pptx_runtime.package import count_registered_slides  # noqa: E402
from shared.pptx_runtime.render import align_rendered_pages, render_pptx  # noqa: E402
from shared.pptx_runtime.thumbnail import create_thumbnail_grids, slide_metadata  # noqa: E402
from shared.slide_spec_contract import validate_slide_spec  # noqa: E402

PPTX_SUFFIXES = {".pptx", ".potx"}


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _existing_file(value: str) -> Path:
    path = _path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file does not exist: {path}")
    return path


def _pptx_file(value: str) -> Path:
    path = _existing_file(value)
    if path.suffix.casefold() not in PPTX_SUFFIXES:
        raise argparse.ArgumentTypeError(f"expected .pptx or .potx: {path}")
    return path


def _directory(value: str) -> Path:
    path = _path(value)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"directory does not exist: {path}")
    return path


def _basename(value: str) -> str:
    if not value or Path(value).name != value or value in {".", ".."}:
        raise argparse.ArgumentTypeError(
            "expected a filename prefix without directory components"
        )
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _slide_count(path: Path) -> int:
    """按 presentation.xml sldIdLst 的注册页数计数（与 render 的 slide_metadata 口径一致）。"""
    return count_registered_slides(path) or 0


def _ensure_separate_output(source: Path, output: Path) -> None:
    if source.resolve() == output.resolve():
        raise SystemExit("refusing to overwrite the source package; choose a different --output")
    output.parent.mkdir(parents=True, exist_ok=True)


def command_inspect(args: argparse.Namespace) -> int:
    path: Path = args.input
    try:
        slide_count = _slide_count(path)
    except (OSError, zipfile.BadZipFile) as exc:
        print(
            json.dumps(
                {"ok": False, "path": str(path), "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    try:
        slides = slide_metadata(path)
        metadata_error = None
    except Exception as exc:  # inspect remains usable for damaged packages; validate reports blockers
        slides = []
        metadata_error = str(exc)
    result: dict[str, Any] = {
        "ok": metadata_error is None,
        "path": str(path),
        "sha256": _sha256(path),
        "slide_count": slide_count,
        "metadata_version": 1,
        "slides": slides,
        "size_bytes": path.stat().st_size,
    }
    if metadata_error:
        result["metadata_warning"] = metadata_error
    if args.text_output:
        output: Path = args.text_output
        output.parent.mkdir(parents=True, exist_ok=True)
        command = shutil.which("markitdown")
        if not command:
            result["ok"] = False
            result["text_extraction"] = "markitdown is unavailable"
        else:
            completed = subprocess.run(
                [command, str(path), "-o", str(output)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            result["text_output"] = str(output)
            result["text_extraction_returncode"] = completed.returncode
            if completed.returncode != 0:
                result["ok"] = False
                result["text_extraction"] = completed.stderr.strip()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


def command_unpack(args: argparse.Namespace) -> int:
    source: Path = args.input
    output: Path = args.output
    output_existed = output.exists()
    if output_existed and not output.is_dir():
        raise SystemExit(f"output path must be a directory: {output}")
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"output directory must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    try:
        safe_extract_package(source, output)
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        if output_existed:
            output.mkdir(parents=True, exist_ok=True)
        raise
    print(json.dumps({"ok": True, "input": str(source), "output": str(output)}))
    return 0


def command_pack(args: argparse.Namespace) -> int:
    source: Path = args.input
    output: Path = args.output
    if output.suffix.casefold() not in PPTX_SUFFIXES:
        raise SystemExit("pack --output must end in .pptx or .potx")
    if output.is_relative_to(source):
        raise SystemExit("pack output must be outside the unpacked input directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    pack_directory(source, output)
    print(
        json.dumps(
            {
                "ok": True,
                "input": str(source),
                "output": str(output),
                "sha256": _sha256(output),
                "slide_count": _slide_count(output),
            },
            ensure_ascii=False,
        )
    )
    return 0


def command_add_slide(args: argparse.Namespace) -> int:
    target: Path = args.input
    if target.is_file():
        output: Path = args.output
        if output.suffix.casefold() not in PPTX_SUFFIXES:
            raise SystemExit("add-slide --output must end in .pptx or .potx")
        _ensure_separate_output(target, output)
        with tempfile.TemporaryDirectory(prefix="pptx-edit-") as tmp:
            unpacked = Path(tmp)
            safe_extract_package(target, unpacked)
            created = add_slide(unpacked, args.source, args.after)
            pack_directory(unpacked, output)
    else:
        if args.output:
            raise SystemExit("--output is not accepted for an unpacked directory")
        created = add_slide(target, args.source, args.after)
    print(json.dumps({"ok": True, "created_slide": created}, ensure_ascii=False))
    return 0


def _package_edit_paths(target: Path, output: Path | None) -> tuple[Path, Path]:
    if output is None:
        raise SystemExit("--output is required for package input to protect the source")
    if output.suffix.casefold() not in PPTX_SUFFIXES:
        raise SystemExit("--output must end in .pptx or .potx")
    _ensure_separate_output(target, output)
    return target, output


def command_delete_slide(args: argparse.Namespace) -> int:
    target: Path = args.input
    if target.is_file():
        source, output = _package_edit_paths(target, args.output)
        with tempfile.TemporaryDirectory(prefix="pptx-edit-") as tmp:
            unpacked = Path(tmp)
            safe_extract_package(source, unpacked)
            delete_slide(unpacked, args.slide)
            clean_package(unpacked)
            pack_directory(unpacked, output)
    else:
        if args.output:
            raise SystemExit("--output is not accepted for an unpacked directory")
        delete_slide(target, args.slide)
    print(json.dumps({"ok": True, "deleted_slide": args.slide}, ensure_ascii=False))
    return 0


def command_reorder_slides(args: argparse.Namespace) -> int:
    target: Path = args.input
    if target.is_file():
        source, output = _package_edit_paths(target, args.output)
        with tempfile.TemporaryDirectory(prefix="pptx-edit-") as tmp:
            unpacked = Path(tmp)
            safe_extract_package(source, unpacked)
            reorder_slides(unpacked, args.slides)
            pack_directory(unpacked, output)
    else:
        if args.output:
            raise SystemExit("--output is not accepted for an unpacked directory")
        reorder_slides(target, args.slides)
    print(json.dumps({"ok": True, "slide_order": args.slides}, ensure_ascii=False))
    return 0


def command_clean(args: argparse.Namespace) -> int:
    try:
        removed = clean_package(args.input)
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "removed": removed}, ensure_ascii=False, indent=2))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    path: Path = args.input
    original: Path | None = args.original
    if not path.is_file():
        print(json.dumps({"ok": False, "findings": [{"code": "input", "part": str(path), "severity": "error", "detail": "validate requires a packed PPTX"}]}))
        return 1
    if original is not None and original.resolve() == path.resolve():
        raise SystemExit("--original 与输入为同一文件；差分去重会把全部 findings 误删，请提供原始源包")
    result = {
        **validate_pptx(path, original),
        "input": str(path),
        "pptx_sha256": _sha256(path) if path.is_file() else None,
        "original": str(original) if original else None,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for finding in result["findings"]:
            print(
                f"[{finding['severity']}] {finding['code']}: "
                f"{finding['part']}: {finding['detail']}"
            )
    return 0 if result["ok"] else 1


def command_normalize_generated(args: argparse.Namespace) -> int:
    try:
        changed = normalize_generated_package(args.input, args.output)
    except FileExistsError as exc:
        raise SystemExit(f"输出已存在，拒绝覆盖: {exc}") from exc
    except (OSError, ValueError) as exc:
        raise SystemExit(f"归一化失败: {exc}") from exc
    print(
        json.dumps(
            {
                "ok": True,
                "input": str(args.input.resolve()),
                "output": str(args.output.resolve()),
                "changed": changed,
            },
            ensure_ascii=False,
        )
    )
    return 0


def command_thumbnail(args: argparse.Namespace) -> int:
    result = create_thumbnail_grids(
        args.input,
        args.output_prefix,
        args.cols,
        args.rows,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "metadata_version": result["metadata_version"],
                "outputs": [str(path) for path in result["outputs"]],
                "slides": result["slides"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_render(args: argparse.Namespace) -> int:
    source: Path = args.input
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        pdf, pages, messages = render_pptx(
            source, output_dir, args.prefix, args.format, args.dpi
        )
    except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "stage": "render", "error": str(exc)}, ensure_ascii=False))
        return 1
    try:
        metadata = slide_metadata(source)
    except Exception as exc:  # 半损坏包：转成干净错误而非 traceback
        print(json.dumps({"ok": False, "stage": "metadata", "error": str(exc)}, ensure_ascii=False))
        return 1
    try:
        pages, hidden_placeholders = align_rendered_pages(
            pages, metadata, output_dir, args.prefix, args.format
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "stage": "render", "error": str(exc)}, ensure_ascii=False))
        return 1
    ok = len(pages) == len(metadata)
    print(
        json.dumps(
            {
                "ok": ok,
                "pptx": str(source),
                "pdf": str(pdf),
                "pages": [str(page) for page in pages],
                "slide_count": len(metadata),
                "rendered_page_count": len(pages),
                "hidden_placeholders": hidden_placeholders,
                "messages": [message for message in messages if message],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ok else 1


def _validate_package_report(report: Path, pptx: Path) -> dict:
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read package report: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("package report root must be an object")
    if data.get("pptx_sha256") != _sha256(pptx):
        raise SystemExit("package report does not match the current PPTX")
    if data.get("ok") is not True:
        raise SystemExit("package report did not pass validation")
    if data.get("validation_profile") != "openxml-sdk-plus-suite-semantic-v4":
        raise SystemExit("package report must use the complete suite validation profile")
    schema = data.get("schema_validation") or {}
    if schema.get("performed") is not True:
        raise SystemExit("package report schema validation was not performed")
    if (schema.get("error_count") or 0) != 0:
        raise SystemExit("package report contains Open XML schema errors")
    return data


def command_qa_manifest(args: argparse.Namespace) -> int:
    pptx: Path = args.pptx
    previews: list[Path] = args.preview
    slide_count = _slide_count(pptx)
    if previews and len(previews) != slide_count:
        raise SystemExit(
            f"preview count ({len(previews)}) must equal slide count ({slide_count}) "
            "when previews are provided"
        )
    package_report_data = None
    if args.package_report:
        package_report_data = _validate_package_report(args.package_report, pptx)
    try:
        spec_report_data = json.loads(args.slide_spec_report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read Slide Spec report: {exc}") from exc
    if not isinstance(spec_report_data, dict) or spec_report_data.get("valid") is not True:
        raise SystemExit("Slide Spec validation report did not pass")
    # 重校验是刻意的完成一致性门禁：捕获 spec 漂移与 spec-vs-pptx 页数不一致，
    # 并非规划期校验（slide_spec_to_pptx_brief）的简单重复。
    try:
        spec_data, spec_errors, actual_spec_hash = validate_slide_spec(args.slide_spec)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot validate Slide Spec: {exc}") from exc
    if spec_errors:
        raise SystemExit(
            "Slide Spec no longer passes validation: "
            + "; ".join(error["message"] for error in spec_errors[:3])
        )
    if len((spec_data or {}).get("slides") or []) != slide_count:
        raise SystemExit("Slide Spec slide count does not match the current PPTX")
    spec_hash = spec_report_data.get("slide_spec_sha256")
    if not spec_hash or actual_spec_hash != spec_hash:
        raise SystemExit("Slide Spec report does not bind the current spec")
    output: Path = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    # scenario_contract_passed 恒为 True：由上方对 Slide Spec 的重校验推导
    # （spec 有效且页数与 slide_count 一致），并非独立的场景检测结果。
    payload = {
        "pptx_sha256": _sha256(pptx),
        "slide_count": slide_count,
        "rendered_page_count": len(previews),
        "scenario_contract_passed": True,
        "slide_spec": str(args.slide_spec),
        "slide_spec_report": str(args.slide_spec_report),
        "slide_spec_report_sha256": _sha256(args.slide_spec_report),
        "slide_spec_sha256": spec_hash,
        "preview_files": [str(path) for path in previews],
        "preview_sha256": [_sha256(path) for path in previews],
    }
    if previews:
        # 视觉检查仅在实际渲染后记录；无 preview 时跳过（视觉检查可选）。
        # completed=True 必须由人工 attestation 支撑：显式提供 --no-repair-needed-reason
        # 且 --remaining-blockers==0；否则不得声称"检查完成"。
        inspection_completed = bool(args.no_repair_needed_reason) and args.remaining_blockers == 0
        payload["visual_inspection"] = {
            "completed": inspection_completed,
            "inspected_pages": list(range(1, slide_count + 1)),
            "repair_cycles": args.repair_cycles,
            "no_repair_needed_reason": args.no_repair_needed_reason,
            "remaining_blockers": args.remaining_blockers,
        }
    if package_report_data is not None:
        payload["package_report"] = str(args.package_report)
        payload["package_report_sha256"] = _sha256(args.package_report)
        payload["package_validation_profile"] = package_report_data.get(
            "validation_profile"
        )
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output)}, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suite-owned PPTX runtime facade")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="inspect a PPTX without modifying it")
    inspect.add_argument("input", type=_pptx_file)
    inspect.add_argument("--text-output", type=_path)
    inspect.set_defaults(handler=command_inspect)

    unpack = sub.add_parser("unpack", help="safely unpack a PPTX")
    unpack.add_argument("input", type=_pptx_file)
    unpack.add_argument("--output", required=True, type=_path)
    unpack.set_defaults(handler=command_unpack)

    pack = sub.add_parser("pack", help="pack an unpacked PPTX directory")
    pack.add_argument("input", type=_directory)
    pack.add_argument("--output", required=True, type=_path)
    pack.set_defaults(handler=command_pack)

    add_slide_parser = sub.add_parser("add-slide", help="add a slide without overwriting a package")
    add_slide_parser.add_argument("input", type=_path)
    add_slide_parser.add_argument("source")
    add_slide_parser.add_argument("--after")
    add_slide_parser.add_argument("--output", type=_path)
    add_slide_parser.set_defaults(handler=command_add_slide)

    delete_slide_parser = sub.add_parser(
        "delete-slide", help="delete a registered slide without overwriting a package"
    )
    delete_slide_parser.add_argument("input", type=_path)
    delete_slide_parser.add_argument("slide")
    delete_slide_parser.add_argument("--output", type=_path)
    delete_slide_parser.set_defaults(handler=command_delete_slide)

    reorder_parser = sub.add_parser(
        "reorder-slides", help="replace the complete slide order without overwriting a package"
    )
    reorder_parser.add_argument("input", type=_path)
    reorder_parser.add_argument("slides", nargs="+")
    reorder_parser.add_argument("--output", type=_path)
    reorder_parser.set_defaults(handler=command_reorder_slides)

    clean = sub.add_parser("clean", help="clean unreferenced parts from an unpacked package")
    clean.add_argument("input", type=_directory)
    clean.set_defaults(handler=command_clean)

    validate = sub.add_parser("validate", help="validate PPTX package and presentation XML")
    validate.add_argument("input", type=_path)
    validate.add_argument("--original", type=_pptx_file)
    validate.add_argument("--json", action="store_true")
    validate.add_argument("--output", type=_path)
    validate.set_defaults(handler=command_validate)

    normalize_generated = sub.add_parser(
        "normalize-generated",
        help="normalize a newly generated package to a distinct non-existing output",
    )
    normalize_generated.add_argument("input", type=_pptx_file)
    normalize_generated.add_argument("--output", required=True, type=_path)
    normalize_generated.set_defaults(handler=command_normalize_generated)

    thumbnail = sub.add_parser("thumbnail", help="create labeled template thumbnail grids")
    thumbnail.add_argument("input", type=_pptx_file)
    thumbnail.add_argument("--output-prefix", required=True, type=_path)
    thumbnail.add_argument("--cols", type=int, default=3)
    thumbnail.add_argument("--rows", type=int, default=4)
    thumbnail.set_defaults(handler=command_thumbnail)

    render = sub.add_parser("render", help="render every slide through LibreOffice and Poppler")
    render.add_argument("input", type=_pptx_file)
    render.add_argument("--output-dir", required=True, type=_path)
    render.add_argument("--prefix", required=True, type=_basename)
    render.add_argument("--format", choices=("jpg", "png"), default="png")
    render.add_argument("--dpi", type=int, default=150)
    render.set_defaults(handler=command_render)

    manifest = sub.add_parser("qa-manifest", help="bind inspected previews to the final PPTX")
    manifest.add_argument("--pptx", required=True, type=_pptx_file)
    manifest.add_argument("--preview", action="append", default=[], type=_existing_file)
    manifest.add_argument("--output", required=True, type=_path)
    manifest.add_argument(
        "--package-report",
        type=_existing_file,
        help="validate-produced package report to bind to the PPTX (optional)",
    )
    manifest.add_argument("--repair-cycles", type=int, default=0)
    manifest.add_argument("--no-repair-needed-reason")
    manifest.add_argument("--remaining-blockers", type=int, default=0)
    manifest.add_argument("--slide-spec-report", required=True, type=_existing_file)
    manifest.add_argument("--slide-spec", required=True, type=_existing_file)
    manifest.set_defaults(handler=command_qa_manifest)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command in {"add-slide", "delete-slide", "reorder-slides"}:
        target: Path = args.input
        if not target.exists() or (
            not target.is_dir() and target.suffix.casefold() not in PPTX_SUFFIXES
        ):
            raise SystemExit(f"expected unpacked directory or .pptx/.potx: {target}")
        if target.is_file() and args.output is None:
            raise SystemExit("--output is required for package input to protect the source")
    raise SystemExit(args.handler(args))


if __name__ == "__main__":
    main()
