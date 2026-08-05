"""Classic DrawingML chart semantic checks.

ChartEx is covered by package/root checks and the Open XML SDK validator. This
module deliberately does not pretend to implement the full ChartEx data model.
"""

from __future__ import annotations

import posixpath
import re
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from ._util import local as _local
from .findings import Finding
from .package import resolve_target

OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL = f"{OFFICE_REL_NS}/package"
R_NS = OFFICE_REL_NS
MAX_WORKBOOK_XML_BYTES = 16 * 1024 * 1024
MAX_WORKBOOK_COMPRESSION_RATIO = 200
MAX_WORKBOOK_MEMBERS = 10_000
PLOT_AXIS_LIMITS = {
    "areaChart": (2, 2),
    "area3DChart": (2, 3),
    "barChart": (2, 3),
    "bar3DChart": (2, 3),
    "bubbleChart": (2, 2),
    "lineChart": (2, 2),
    "line3DChart": (3, 3),
    "radarChart": (2, 2),
    "scatterChart": (2, 2),
    "stockChart": (2, 2),
    "surfaceChart": (3, 3),
    "surface3DChart": (3, 3),
}
_CELL_RANGE = re.compile(
    r"^(?:\[[^]]+\])?(?:'((?:[^']|'')+)'|([^'!]+))!"
    r"\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?$",
    re.IGNORECASE,
)


def _parse(path: Path, part: str, findings: list[Finding]):
    try:
        return ET.parse(path).getroot()
    except Exception as exc:
        findings.append(Finding("xml-parse", part, str(exc)))
        return None


def _column_number(value: str) -> int:
    result = 0
    for character in value.upper():
        result = result * 26 + ord(character) - ord("A") + 1
    return result


def _formula_points(formula: str) -> int | None:
    matched = _CELL_RANGE.match(formula.strip())
    if not matched:
        return None
    start_column = _column_number(matched.group(3))
    start_row = int(matched.group(4))
    end_column = _column_number(matched.group(5) or matched.group(3))
    end_row = int(matched.group(6) or matched.group(4))
    if end_column < start_column or end_row < start_row:
        return None
    return (end_column - start_column + 1) * (end_row - start_row + 1)


def _formula_sheet(formula: str) -> str | None:
    matched = _CELL_RANGE.match(formula.strip())
    if not matched:
        return None
    return (matched.group(1) or matched.group(2) or "").replace("''", "'")


def _cache_point_count(part: str, container, findings: list[Finding]) -> int | None:
    cache = container if _local(container.tag) in {"numLit", "strLit"} else next(
        (child for child in container if _local(child.tag) in {"numCache", "strCache"}),
        None,
    )
    if cache is None:
        return None
    declared_node = next((child for child in cache if _local(child.tag) == "ptCount"), None)
    declared_text = declared_node.attrib.get("val") if declared_node is not None else None
    try:
        declared = int(declared_text) if declared_text is not None else None
    except ValueError:
        declared = None
    points = [child for child in cache if _local(child.tag) == "pt"]
    indexes = [child.attrib.get("idx", "") for child in points]
    if declared is None or declared < 0:
        findings.append(Finding("chart-cache-count", part, f"{_local(container.tag)} has invalid ptCount"))
    elif len(points) > declared:
        findings.append(
            Finding(
                "chart-cache-count",
                part,
                f"{_local(container.tag)} declares {declared} points but contains {len(points)}",
            )
        )
    if len(indexes) != len(set(indexes)) or any(not value.isdigit() for value in indexes):
        findings.append(
            Finding("chart-cache-index", part, f"{_local(container.tag)} has invalid or duplicate pt idx")
        )
    elif declared is not None and any(int(value) >= declared for value in indexes):
        findings.append(
            Finding("chart-cache-index", part, f"{_local(container.tag)} has pt idx outside ptCount")
        )
    if _local(cache.tag) in {"numCache", "numLit"}:
        for point in points:
            value = next((child.text for child in point if _local(child.tag) == "v"), None)
            try:
                float(value) if value not in {None, ""} else None
            except ValueError:
                findings.append(Finding("chart-cache-number", part, f"non-numeric cached value: {value}"))
    formula = next((child.text for child in container if _local(child.tag) == "f"), None)
    formula_points = _formula_points(formula) if formula else None
    if formula and formula_points is None:
        findings.append(
            Finding(
                "chart-formula",
                part,
                f"named, dynamic, or unsupported chart formula was not range-checked: {formula}",
                "info",
            )
        )
    elif formula_points is not None and declared is not None and formula_points != declared:
        findings.append(
            Finding(
                "chart-formula-cache-count",
                part,
                f"formula spans {formula_points} cells but cache declares {declared}: {formula}",
                "warning",
            )
        )
    return declared


def _validate_chart_caches(part: str, chart, findings: list[Finding]) -> None:
    for series in (node for node in chart.iter() if _local(node.tag) == "ser"):
        counts: dict[str, int] = {}
        for field in series:
            field_name = _local(field.tag)
            if field_name not in {"cat", "val", "xVal", "yVal", "bubbleSize"}:
                continue
            reference = next(
                (
                    child
                    for child in field
                    if _local(child.tag) in {"numRef", "strRef", "numLit", "strLit"}
                ),
                None,
            )
            if reference is not None:
                count = _cache_point_count(part, reference, findings)
                if count is not None:
                    counts[field_name] = count
        for left, right in (("cat", "val"), ("xVal", "yVal"), ("yVal", "bubbleSize")):
            if left in counts and right in counts and counts[left] != counts[right]:
                findings.append(
                    Finding(
                        "chart-series-cardinality",
                        part,
                        f"series {left} has {counts[left]} points but {right} has {counts[right]}",
                        "warning",
                    )
                )


def _relationship_details(root: Path, source: str) -> dict[str, tuple[str, str]]:
    rels = root / Path(source).parent / "_rels" / f"{Path(source).name}.rels"
    if not rels.is_file():
        return {}
    details = {}
    for relation in ET.parse(rels).getroot():
        if relation.attrib.get("TargetMode") == "External":
            continue
        target = relation.attrib.get("Target")
        if target:
            details[relation.attrib.get("Id", "")] = (
                relation.attrib.get("Type", ""),
                resolve_target(source, target),
            )
    return details


def _read_workbook_xml(workbook: zipfile.ZipFile, name: str) -> bytes:
    info = workbook.getinfo(name)
    if info.file_size > MAX_WORKBOOK_XML_BYTES:
        raise ValueError(f"embedded workbook member exceeds safety limit: {name}")
    if info.file_size / max(info.compress_size, 1) > MAX_WORKBOOK_COMPRESSION_RATIO:
        raise ValueError(f"embedded workbook member exceeds compression-ratio limit: {name}")
    return workbook.read(info)


def _embedded_workbook_sheets(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as workbook:
        members = workbook.infolist()
        if len(members) > MAX_WORKBOOK_MEMBERS:
            raise ValueError(f"embedded workbook has too many members: {len(members)}")
        workbook_xml = ET.fromstring(_read_workbook_xml(workbook, "xl/workbook.xml"))
        rels_xml = ET.fromstring(_read_workbook_xml(workbook, "xl/_rels/workbook.xml.rels"))
        rel_targets = {}
        for relation in rels_xml:
            if relation.attrib.get("TargetMode") == "External":
                continue
            target = relation.attrib.get("Target")
            if target:
                resolved = (
                    posixpath.normpath(target.lstrip("/"))
                    if target.startswith("/")
                    else posixpath.normpath(posixpath.join("xl", target))
                )
                if resolved == ".." or resolved.startswith("../"):
                    raise ValueError(f"embedded workbook relationship escapes package: {target}")
                rel_targets[relation.attrib.get("Id", "")] = resolved
        names = {info.filename for info in members}
        sheets = set()
        for sheet in workbook_xml.iter():
            if _local(sheet.tag) != "sheet":
                continue
            rid = sheet.attrib.get(f"{{{R_NS}}}id", "")
            if rid in rel_targets and rel_targets[rid] in names and sheet.attrib.get("name"):
                sheets.add(sheet.attrib["name"])
        return sheets


def _validate_chart_external_data(
    root: Path,
    part: str,
    chart,
    files: set[str],
    findings: list[Finding],
) -> None:
    formulas = [node.text for node in chart.iter() if _local(node.tag) == "f" and node.text]
    relations = _relationship_details(root, part)
    workbook_targets: set[str] = set()
    for node in (node for node in chart.iter() if _local(node.tag) == "externalData"):
        rid = node.attrib.get(f"{{{R_NS}}}id", "")
        relation = relations.get(rid)
        if relation is None:
            findings.append(
                Finding("chart-external-data-relationship", part, f"unresolved externalData r:id: {rid}")
            )
            continue
        relation_type, target = relation
        if relation_type != PACKAGE_REL:
            findings.append(
                Finding("chart-external-data-type", part, f"{rid} is not an embedded package relationship")
            )
        if target not in files or Path(target).suffix.casefold() not in {".xlsx", ".xlsm"}:
            findings.append(Finding("chart-external-data-target", part, f"invalid workbook: {target}"))
            continue
        workbook_targets.add(target)
    if formulas and not workbook_targets:
        # 公式引用了工作簿却无有效 embedded workbook，属于真实数据缺陷，阻断交付。
        findings.append(
            Finding(
                "chart-workbook-missing",
                part,
                "chart contains worksheet formulas but has no valid embedded workbook",
                "error",
            )
        )
        return
    referenced_sheets = {sheet for formula in formulas if (sheet := _formula_sheet(formula))}
    for target in sorted(workbook_targets):
        try:
            available_sheets = _embedded_workbook_sheets(root / Path(target))
        except (KeyError, OSError, ValueError, zipfile.BadZipFile) as exc:
            findings.append(Finding("chart-workbook-unreadable", target, str(exc)))
            continue
        for missing in sorted(referenced_sheets - available_sheets):
            findings.append(Finding("chart-formula-sheet-missing", part, f"{missing} is absent from {target}"))


def validate_charts(root: Path, files: set[str], findings: list[Finding]) -> None:
    """Validate classic chart parts; ChartEx remains SDK-validated only."""
    for part in sorted(
        name
        for name in files
        if name.startswith("ppt/charts/chart")
        and not name.startswith("ppt/charts/chartEx")
        and name.endswith(".xml")
    ):
        chart = _parse(root / Path(part), part, findings)
        if chart is None:
            continue
        declared: set[str] = set()
        duplicate_declared: set[str] = set()
        referenced: set[str] = set()
        axis_crosses: dict[str, str] = {}
        for node in chart.iter():
            name = _local(node.tag)
            if name in {"catAx", "valAx", "dateAx", "serAx"}:
                axis_id = None
                cross_axis = None
                for child in node:
                    if _local(child.tag) == "axId" and child.attrib.get("val"):
                        axis_id = child.attrib["val"]
                        if axis_id in declared:
                            duplicate_declared.add(axis_id)
                        declared.add(axis_id)
                    elif _local(child.tag) == "crossAx" and child.attrib.get("val"):
                        cross_axis = child.attrib["val"]
                if axis_id and cross_axis:
                    axis_crosses[axis_id] = cross_axis
                elif axis_id:
                    findings.append(Finding("chart-axis-cross-missing", part, f"axis {axis_id} has no crossAx"))
            elif name in {"crossAx", "axId"} and node.attrib.get("val"):
                referenced.add(node.attrib["val"])
        for plot in chart.iter():
            plot_name = _local(plot.tag)
            if plot_name in PLOT_AXIS_LIMITS:
                plot_axes = [
                    child.attrib["val"]
                    for child in plot
                    if _local(child.tag) == "axId" and child.attrib.get("val")
                ]
                minimum, maximum = PLOT_AXIS_LIMITS[plot_name]
                if not minimum <= len(plot_axes) <= maximum:
                    findings.append(
                        Finding(
                            "chart-axis-cardinality",
                            part,
                            f"{plot_name} declares {len(plot_axes)} axes; expected {minimum}-{maximum}",
                        )
                    )
                if len(plot_axes) != len(set(plot_axes)):
                    findings.append(Finding("chart-plot-axis-duplicate", part, f"{plot_name} repeats an axis id"))
            series = [child for child in plot if _local(child.tag) == "ser"]
            for field in ("idx", "order"):
                values = [
                    child.attrib.get("val", "")
                    for item in series
                    for child in item
                    if _local(child.tag) == field
                ]
                if len(values) != len(series) or len(values) != len(set(values)):
                    findings.append(
                        Finding(
                            f"chart-series-{field}",
                            part,
                            f"{plot_name} series require one unique {field} each",
                        )
                    )
            if plot_name in {"barChart", "bar3DChart"}:
                grouping = next(
                    (child.attrib.get("val") for child in plot if _local(child.tag) == "grouping"),
                    None,
                )
                if grouping in {"stacked", "percentStacked"} and any(
                    _local(node.tag) == "dLblPos" and node.attrib.get("val") == "outEnd"
                    for node in plot.iter()
                ):
                    findings.append(
                        Finding("stacked-label-position", part, "stacked bar/column chart uses outEnd")
                    )
        for missing in sorted(referenced - declared):
            findings.append(
                Finding(
                    "chart-axis-missing",
                    part,
                    f"chart references an axis not declared in this chart part: {missing}",
                    # Official skill treats an undeclared axis reference as a
                    # PowerPoint-refused defect, not a warning.
                    "error",
                )
            )
        for duplicate in sorted(duplicate_declared):
            findings.append(Finding("chart-axis-duplicate", part, f"axis id is duplicated: {duplicate}"))
        for axis_id, cross_axis in sorted(axis_crosses.items()):
            if cross_axis == axis_id:
                findings.append(Finding("chart-axis-self-cross", part, f"axis {axis_id} crosses itself"))
            elif cross_axis in axis_crosses and axis_crosses[cross_axis] != axis_id:
                findings.append(
                    Finding(
                        "chart-axis-cross-nonreciprocal",
                        part,
                        f"axis {axis_id} crosses {cross_axis}, which crosses {axis_crosses[cross_axis]}",
                    )
                )
        for parent in chart.iter():
            children = list(parent)
            extension_indexes = [
                index for index, child in enumerate(children) if _local(child.tag) == "extLst"
            ]
            if len(extension_indexes) > 1:
                findings.append(
                    Finding("chart-ext-list-duplicate", part, f"{_local(parent.tag)} has multiple extLst")
                )
            if extension_indexes and extension_indexes[-1] != len(children) - 1:
                findings.append(
                    Finding("chart-ext-list-order", part, f"extLst is not last in {_local(parent.tag)}")
                )
        _validate_chart_caches(part, chart, findings)
        _validate_chart_external_data(root, part, chart, files, findings)
