"""PPTX-only package, relationship, presentation, and chart validation."""

from __future__ import annotations

import tempfile
import zipfile
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from defusedxml import ElementTree as ET

from .charts import validate_charts
from .findings import Finding
from .openxml import OPENXML_SDK_VERSION, validate_openxml
from .package import relationship_source, resolve_target, safe_extract_package

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SLIDE_REL = f"{OFFICE_REL_NS}/slide"
SLIDE_LAYOUT_REL = f"{OFFICE_REL_NS}/slideLayout"
SLIDE_MASTER_REL = f"{OFFICE_REL_NS}/slideMaster"
THEME_REL = f"{OFFICE_REL_NS}/theme"
NOTES_MASTER_REL = f"{OFFICE_REL_NS}/notesMaster"
R_NS = OFFICE_REL_NS
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
CHARTEX_NS = "http://schemas.microsoft.com/office/drawing/2014/chartex"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse(path: Path, part: str, findings: list[Finding]):
    try:
        return ET.parse(path).getroot()
    except Exception as exc:
        findings.append(Finding("xml-parse", part, str(exc)))
        return None


def _validate_relationships(root: Path, files: set[str], findings: list[Finding]) -> dict[str, dict[str, str]]:
    relationships: dict[str, dict[str, str]] = {}
    for rels_name in sorted(name for name in files if name.endswith(".rels")):
        try:
            source = relationship_source(rels_name)
        except ValueError as exc:
            findings.append(Finding("relationship-part", rels_name, str(exc)))
            continue
        if source is not None and source not in files:
            findings.append(
                Finding("relationship-source-missing", rels_name, f"source part is absent: {source}")
            )
        rels_root = _parse(root / Path(rels_name), rels_name, findings)
        if rels_root is None:
            continue
        if rels_root.tag != f"{{{REL_NS}}}Relationships":
            findings.append(
                Finding("relationship-root", rels_name, f"unexpected root element: {rels_root.tag}")
            )
        ids: set[str] = set()
        source_map: dict[str, str] = {}
        for rel in rels_root:
            if rel.tag != f"{{{REL_NS}}}Relationship":
                findings.append(
                    Finding("relationship-element", rels_name, f"unexpected child element: {rel.tag}")
                )
                continue
            rid = rel.attrib.get("Id", "")
            if not rid or rid in ids:
                findings.append(Finding("relationship-id", rels_name, f"missing or duplicate Id: {rid}"))
            ids.add(rid)
            if not rel.attrib.get("Type"):
                findings.append(Finding("relationship-type", rels_name, f"{rid} has no Type"))
            target_mode = rel.attrib.get("TargetMode")
            if target_mode not in {None, "Internal", "External"}:
                findings.append(
                    Finding("relationship-target-mode", rels_name, f"{rid} has invalid TargetMode: {target_mode}")
                )
            if target_mode == "External":
                continue
            target = rel.attrib.get("Target")
            if not target:
                findings.append(Finding("relationship-target", rels_name, f"{rid} has no Target"))
                continue
            try:
                resolved = resolve_target(source, target)
            except ValueError as exc:
                findings.append(Finding("relationship-target", rels_name, str(exc)))
                continue
            if resolved not in files:
                findings.append(Finding("relationship-missing-part", rels_name, f"{rid} -> {resolved}"))
            source_map[rid] = resolved
        relationships[source or ""] = source_map
    return relationships


def _validate_relationship_references(
    root: Path,
    files: set[str],
    findings: list[Finding],
) -> None:
    for part in sorted(name for name in files if name.endswith(".xml")):
        xml_root = _parse(root / Path(part), part, findings)
        if xml_root is None:
            continue
        rels_name = (
            str(Path(part).parent / "_rels" / f"{Path(part).name}.rels")
            .replace("\\", "/")
        )
        declared: set[str] = set()
        if rels_name in files:
            rels_root = _parse(root / Path(rels_name), rels_name, findings)
            if rels_root is not None:
                declared = {rel.attrib.get("Id", "") for rel in rels_root}
        used = {
            value
            for node in xml_root.iter()
            for attribute, value in node.attrib.items()
            if attribute.startswith(f"{{{OFFICE_REL_NS}}}")
            and _local(attribute) in {"id", "embed", "link"}
        }
        for missing in sorted(used - declared):
            findings.append(
                Finding("relationship-id-unresolved", part, f"relationship id is not declared: {missing}")
            )


def _validate_content_types(root: Path, files: set[str], findings: list[Finding]) -> None:
    part = "[Content_Types].xml"
    types = _parse(root / part, part, findings)
    if types is None:
        return
    if types.tag != f"{{{CONTENT_TYPES_NS}}}Types":
        findings.append(Finding("content-types-root", part, f"unexpected root element: {types.tag}"))
    defaults: set[str] = set()
    overrides: set[str] = set()
    for item in types:
        item_name = _local(item.tag)
        content_type = item.attrib.get("ContentType", "")
        if not content_type:
            findings.append(Finding("content-type-empty", part, f"{item_name} has no ContentType"))
        if item_name == "Default":
            extension = item.attrib.get("Extension", "").casefold()
            if not extension or "/" in extension or "\\" in extension:
                findings.append(Finding("content-type-extension", part, f"invalid extension: {extension}"))
            if extension in defaults:
                findings.append(Finding("content-type-default-duplicate", part, extension))
            defaults.add(extension)
        elif item_name == "Override":
            raw_name = item.attrib.get("PartName", "")
            if not raw_name.startswith("/") or ".." in Path(raw_name).parts:
                findings.append(Finding("content-type-part-name", part, f"invalid PartName: {raw_name}"))
            name = raw_name.lstrip("/")
            if name in overrides:
                findings.append(Finding("content-type-override-duplicate", part, name))
            overrides.add(name)
        else:
            findings.append(Finding("content-type-element", part, f"unexpected child: {item.tag}"))
    for name in files - {part}:
        extension = "rels" if name.endswith(".rels") else Path(name).suffix.lstrip(".").casefold()
        if name not in overrides and extension not in defaults:
            findings.append(Finding("content-type-missing", name, "no Default or Override entry"))
    for override in sorted(overrides - files):
        findings.append(
            Finding(
                "content-type-orphan",
                part,
                override,
                "warning",
            )
        )


def _validate_presentation(root: Path, relationships: dict[str, dict[str, str]], findings: list[Finding]) -> None:
    part = "ppt/presentation.xml"
    presentation = _parse(root / part, part, findings)
    if presentation is None:
        return
    seen_ids: set[str] = set()
    seen_rids: set[str] = set()
    rels = relationships.get(part, {})
    for slide in presentation.findall(f".//{{{P_NS}}}sldId"):
        slide_id = slide.attrib.get("id", "")
        rid = slide.attrib.get(f"{{{R_NS}}}id", "")
        if not slide_id or slide_id in seen_ids:
            findings.append(Finding("slide-id", part, f"missing or duplicate id: {slide_id}"))
        if not rid or rid in seen_rids:
            findings.append(Finding("slide-rid", part, f"missing or duplicate r:id: {rid}"))
        seen_ids.add(slide_id)
        seen_rids.add(rid)
        target = rels.get(rid)
        if not target or not target.startswith("ppt/slides/slide"):
            findings.append(Finding("slide-relationship", part, f"{rid} is not a registered slide"))
    if not seen_rids:
        findings.append(Finding("presentation-empty", part, "presentation contains no slides"))


def _validate_part_roots(root: Path, files: set[str], findings: list[Finding]) -> None:
    expected = (
        ("ppt/slides/slide", ".xml", P_NS, "sld"),
        ("ppt/slideLayouts/slideLayout", ".xml", P_NS, "sldLayout"),
        ("ppt/slideMasters/slideMaster", ".xml", P_NS, "sldMaster"),
        ("ppt/notesSlides/notesSlide", ".xml", P_NS, "notes"),
        ("ppt/notesMasters/notesMaster", ".xml", P_NS, "notesMaster"),
        ("ppt/charts/chartEx", ".xml", CHARTEX_NS, "chartSpace"),
        ("ppt/charts/chart", ".xml", CHART_NS, "chartSpace"),
        ("ppt/theme/theme", ".xml", DRAWING_NS, "theme"),
    )
    for part in sorted(files):
        rule = next(
            (item for item in expected if part.startswith(item[0]) and part.endswith(item[1])),
            None,
        )
        if rule is None:
            continue
        parsed = _parse(root / Path(part), part, findings)
        if parsed is None:
            continue
        wanted = f"{{{rule[2]}}}{rule[3]}"
        if parsed.tag != wanted:
            findings.append(
                Finding("part-root", part, f"expected {wanted}, found {parsed.tag}")
            )


def _relationship_records(root: Path, source: str) -> list[tuple[str, str]]:
    rels = root / Path(source).parent / "_rels" / f"{Path(source).name}.rels"
    if not rels.is_file():
        return []
    records = []
    for relation in ET.parse(rels).getroot():
        if relation.attrib.get("TargetMode") == "External":
            continue
        target = relation.attrib.get("Target")
        if target:
            records.append((relation.attrib.get("Type", ""), resolve_target(source, target)))
    return records


def _validate_notes(root: Path, files: set[str], findings: list[Finding]) -> None:
    for part in sorted(
        name for name in files if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
    ):
        records = _relationship_records(root, part)
        slides = [target for kind, target in records if kind == SLIDE_REL]
        masters = [target for kind, target in records if kind == NOTES_MASTER_REL]
        if len(slides) != 1:
            findings.append(
                Finding("notes-slide-reference", part, f"expected one slide relationship, found {len(slides)}")
            )
        if len(masters) != 1:
            findings.append(
                Finding("notes-master-reference", part, f"expected one notes master relationship, found {len(masters)}")
            )


def _validate_master_themes(root: Path, files: set[str], findings: list[Finding]) -> None:
    master_prefixes = (
        "ppt/slideMasters/slideMaster",
        "ppt/notesMasters/notesMaster",
        "ppt/handoutMasters/handoutMaster",
    )
    masters = sorted(
        (
            name
            for name in files
            if name.startswith(master_prefixes) and name.endswith(".xml")
        ),
        key=lambda name: next(
            index for index, prefix in enumerate(master_prefixes) if name.startswith(prefix)
        ),
    )
    owners: dict[str, list[str]] = defaultdict(list)
    master_slides: dict[str, set[str]] = defaultdict(set)
    layout_master: dict[str, str] = {}
    for layout in sorted(
        name for name in files if name.startswith("ppt/slideLayouts/slideLayout") and name.endswith(".xml")
    ):
        master_targets = [
            target
            for kind, target in _relationship_records(root, layout)
            if kind == SLIDE_MASTER_REL and target in files
        ]
        if len(master_targets) == 1:
            layout_master[layout] = master_targets[0]
    for slide in sorted(
        name for name in files if name.startswith("ppt/slides/slide") and name.endswith(".xml")
    ):
        for kind, layout in _relationship_records(root, slide):
            if kind == SLIDE_LAYOUT_REL and layout in layout_master:
                master_slides[layout_master[layout]].add(slide)
    for master in masters:
        for kind, target in _relationship_records(root, master):
            if kind == THEME_REL and target in files:
                owners[target].append(master)

    for theme, theme_masters in sorted(owners.items()):
        if len(theme_masters) < 2:
            continue
        findings.append(
            Finding(
                "shared-master-theme",
                theme,
                f"shared by {len(theme_masters)} masters: {', '.join(theme_masters)}",
                "info",
            )
        )
    for master, slides in sorted(master_slides.items()):
        if len(slides) > 1:
            findings.append(
                Finding(
                    "shared-slide-master",
                    master,
                    f"editing this master can affect {len(slides)} slides",
                    "info",
                )
            )


def _validate_unpacked(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    required = {"[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml", "ppt/_rels/presentation.xml.rels"}
    for missing in sorted(required - files):
        findings.append(Finding("required-part-missing", missing, "required PPTX part is absent"))
    for path in sorted(root.rglob("*.xml")) + sorted(root.rglob("*.rels")):
        _parse(path, path.relative_to(root).as_posix(), findings)
    relationships = _validate_relationships(root, files, findings)
    _validate_relationship_references(root, files, findings)
    if "[Content_Types].xml" in files:
        _validate_content_types(root, files, findings)
    if "ppt/presentation.xml" in files:
        _validate_presentation(root, relationships, findings)
    _validate_part_roots(root, files, findings)
    _validate_notes(root, files, findings)
    _validate_master_themes(root, files, findings)
    validate_charts(root, files, findings)
    return findings


def _schema_findings(path: Path) -> tuple[list[Finding], dict]:
    try:
        result = validate_openxml(path)
    except RuntimeError as exc:
        return (
            [Finding("schema-validator-unavailable", str(path), str(exc))],
            {
                "performed": False,
                "engine": "DocumentFormat.OpenXml",
                "sdk_package_version": OPENXML_SDK_VERSION,
                "reason": str(exc),
            },
        )
    errors = result.get("errors", [])
    if result.get("fatal"):
        errors = [result]
    findings = []
    for error in errors:
        location = error.get("part") or str(path)
        detail = error.get("description", "Open XML schema validation failed")
        if error.get("path"):
            detail = f"{detail} ({error['path']})"
        findings.append(
            Finding(
                f"openxml-{error.get('id') or error.get('error_type') or 'schema'}",
                location,
                detail,
            )
        )
    status = {
        "performed": True,
        "engine": result.get("engine", "DocumentFormat.OpenXml"),
        "engine_version": result.get("engine_version"),
        "sdk_package_version": result.get("sdk_package_version", OPENXML_SDK_VERSION),
        "target": result.get("target", "Microsoft365"),
        "max_errors": result.get("max_errors"),
        "truncated": bool(result.get("truncated")),
        "error_count": len(findings),
    }
    return findings, status


def validate_pptx(path: Path, original: Path | None = None) -> dict:
    try:
        with tempfile.TemporaryDirectory(prefix="pptx-validate-") as tmp:
            root = Path(tmp)
            safe_extract_package(path, root)
            findings = _validate_unpacked(root)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        findings = [Finding("package-unreadable", str(path), str(exc))]
    schema_findings, schema_status = _schema_findings(path)
    findings.extend(schema_findings)
    if original:
        try:
            with tempfile.TemporaryDirectory(prefix="pptx-original-") as tmp:
                original_root = Path(tmp)
                safe_extract_package(original, original_root)
                baseline = set(_validate_unpacked(original_root))
        except (OSError, ValueError, zipfile.BadZipFile):
            baseline = set()
        original_schema, _ = _schema_findings(original)
        baseline.update(original_schema)
        findings = [finding for finding in findings if finding not in baseline]
    if schema_status.get("performed"):
        schema_status["error_count"] = sum(
            finding.severity == "error"
            and (finding.code.startswith("openxml-") or finding.code == "schema-validator-unavailable")
            for finding in findings
        )
    payload = [asdict(finding) for finding in findings]
    error_count = sum(finding.severity == "error" for finding in findings)
    return {
        "ok": error_count == 0,
        "validation_profile": "openxml-sdk-plus-suite-semantic-v4",
        "schema_validation": schema_status,
        "findings": payload,
        "finding_count": len(payload),
        "error_count": error_count,
        "warning_count": sum(finding.severity == "warning" for finding in findings),
        "info_count": sum(finding.severity == "info" for finding in findings),
    }
