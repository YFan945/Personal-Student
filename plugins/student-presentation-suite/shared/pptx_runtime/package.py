"""Safe PPTX package primitives."""

from __future__ import annotations

import posixpath
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

MAX_PACKAGE_MEMBERS = 10_000
MAX_MEMBER_BYTES = 256 * 1024 * 1024
MAX_PACKAGE_BYTES = 512 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200
COMPRESSION_RATIO_MIN_BYTES = 10 * 1024 * 1024


def _safe_member(name: str) -> PurePosixPath:
    normalized = PurePosixPath(name.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError(f"unsafe package member: {name}")
    return normalized


def safe_extract_package(package: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    root = output.resolve()
    with zipfile.ZipFile(package) as archive:
        members = archive.infolist()
        if len(members) > MAX_PACKAGE_MEMBERS:
            raise ValueError(f"PPTX package has too many members: {len(members)}")
        if sum(info.file_size for info in members) > MAX_PACKAGE_BYTES:
            raise ValueError("PPTX package uncompressed size exceeds the safety limit")
        for info in members:
            if info.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f"PPTX package member exceeds the safety limit: {info.filename}")
            if (
                info.file_size >= COMPRESSION_RATIO_MIN_BYTES
                and info.file_size / max(info.compress_size, 1) > MAX_COMPRESSION_RATIO
            ):
                raise ValueError(
                    f"PPTX package member exceeds the compression-ratio limit: {info.filename}"
                )
            member = _safe_member(info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"symbolic links are not allowed in PPTX packages: {info.filename}")
            destination = (output / Path(*member.parts)).resolve()
            if destination != root and root not in destination.parents:
                raise ValueError(f"package member escapes output directory: {info.filename}")
            if info.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open("wb") as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)


def pack_directory(source: Path, output: Path) -> None:
    source = source.resolve()
    output = output.resolve()
    if output.is_relative_to(source):
        raise ValueError("pack output must be outside the unpacked directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        paths = sorted(item for item in source.rglob("*") if item.is_file())
        if len(paths) > MAX_PACKAGE_MEMBERS:
            raise ValueError(f"unpacked package has too many members: {len(paths)}")
        total_bytes = 0
        for path in paths:
            if path.is_symlink():
                raise ValueError(f"symbolic links are not allowed in PPTX packages: {path}")
            size = path.stat().st_size
            if size > MAX_MEMBER_BYTES:
                raise ValueError(f"unpacked package member exceeds the safety limit: {path}")
            total_bytes += size
        if total_bytes > MAX_PACKAGE_BYTES:
            raise ValueError("unpacked package size exceeds the safety limit")
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in paths:
                info = zipfile.ZipInfo(
                    path.relative_to(source).as_posix(),
                    date_time=(1980, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                with path.open("rb") as source_file, archive.open(info, "w") as target:
                    shutil.copyfileobj(source_file, target, length=1024 * 1024)
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()


def relationship_source(rels_name: str) -> str | None:
    rels = PurePosixPath(rels_name)
    if rels.as_posix() == "_rels/.rels":
        return None
    if rels.parent.name != "_rels" or not rels.name.endswith(".rels"):
        raise ValueError(f"not a relationship part: {rels_name}")
    source_name = rels.name.removesuffix(".rels")
    return (rels.parent.parent / source_name).as_posix()


def relationship_part(source: str) -> str:
    part = PurePosixPath(source)
    return (part.parent / "_rels" / f"{part.name}.rels").as_posix()


def resolve_target(source: str | None, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    base = "" if source is None else posixpath.dirname(source)
    resolved = posixpath.normpath(posixpath.join(base, target))
    if resolved == ".." or resolved.startswith("../"):
        raise ValueError(f"relationship target escapes package: {target}")
    return resolved


PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


def count_registered_slides(package: Path) -> int | None:
    """Return the number of slides registered in ``presentation.xml sldIdLst``.

    Counts the direct ``<p:sldId>`` children of the main ``<p:sldIdLst>`` only
    (custom-show ``sldId`` entries are excluded). Returns ``None`` when the
    presentation part is missing or unreadable.
    """
    try:
        with zipfile.ZipFile(package) as archive, archive.open("ppt/presentation.xml") as stream:
            text = stream.read()
    except (KeyError, zipfile.BadZipFile, OSError):
        return None
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None
    lst = root.find(f"{{{PRESENTATION_NS}}}sldIdLst")
    if lst is None:
        return 0
    return sum(
        1
        for child in lst
        if child.tag == f"{{{PRESENTATION_NS}}}sldId"
    )
