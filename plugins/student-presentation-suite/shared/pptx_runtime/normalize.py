"""Normalize generated PPTX structures before schema validation.

Only fixes structures that cannot pass validation without mutation. The
<p:presentation> child order that pptxgenjs writes (notesMasterIdLst directly
after sldIdLst) is left untouched on disk: PowerPoint reads that order, and the
official pptx skill says never to reorder it. Schema validation reorders a
temporary copy instead (see validate._schema_preprocessed_package).
"""

from __future__ import annotations

import tempfile
import xml.etree.ElementTree as StdET
from pathlib import Path

from defusedxml import ElementTree as ET

from .package import pack_directory, safe_extract_package

C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
StdET.register_namespace("c", C_NS)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize_unpacked(root: Path) -> list[str]:
    changed: list[str] = []
    charts_root = root / "ppt" / "charts"
    for chart_path in sorted(charts_root.glob("chart*.xml")) if charts_root.is_dir() else []:
        chart = ET.parse(chart_path).getroot()
        plot_area = chart.find(f".//{{{C_NS}}}plotArea")
        if plot_area is None:
            continue
        declared_axes = {
            axis_id.get("val")
            for axis_name in ("catAx", "dateAx", "valAx", "serAx")
            for axis in plot_area.findall(f"{{{C_NS}}}{axis_name}")
            for axis_id in axis.findall(f"{{{C_NS}}}axId")
            if axis_id.get("val")
        }
        chart_changed = False
        for chart_node in list(plot_area):
            if not _local(chart_node.tag).endswith("Chart"):
                continue
            for axis_id in list(chart_node.findall(f"{{{C_NS}}}axId")):
                if axis_id.get("val") not in declared_axes:
                    chart_node.remove(axis_id)
                    chart_changed = True
        if chart_changed:
            StdET.ElementTree(chart).write(
                chart_path,
                encoding="utf-8",
                xml_declaration=True,
            )
            changed.append(chart_path.relative_to(root).as_posix())
    return changed


def normalize_generated_package(source: Path, output: Path) -> list[str]:
    source = source.resolve()
    output = output.resolve()
    if source == output:
        raise ValueError("normalization output must differ from the generated source")
    if output.exists():
        raise FileExistsError(f"normalization output already exists: {output}")
    with tempfile.TemporaryDirectory(prefix="pptx-normalize-") as tmp:
        unpacked = Path(tmp) / "package"
        safe_extract_package(source, unpacked)
        changed = normalize_unpacked(unpacked)
        pack_directory(unpacked, output)
    return changed
