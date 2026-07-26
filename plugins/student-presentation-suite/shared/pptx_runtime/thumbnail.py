"""Labeled, paginated PPTX contact sheets with hidden-slide awareness."""

from __future__ import annotations

import posixpath
import tempfile
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

from .package import resolve_target
from .render import render_pptx

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
SLIDE_LAYOUT_REL = f"{R_NS}/slideLayout"
NOTES_SLIDE_REL = f"{R_NS}/notesSlide"
CHART_REL = f"{R_NS}/chart"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _part_relationships(archive: zipfile.ZipFile, part: str) -> list[dict[str, str]]:
    part_path = posixpath.dirname(part)
    rels_name = posixpath.join(part_path, "_rels", posixpath.basename(part) + ".rels")
    if rels_name not in archive.namelist():
        return []
    return [
        {
            "id": relation.attrib.get("Id", ""),
            "type": relation.attrib.get("Type", ""),
            "target": resolve_target(part, relation.attrib.get("Target", "")),
        }
        for relation in ET.fromstring(archive.read(rels_name))
        if relation.attrib.get("Target") and relation.attrib.get("TargetMode") != "External"
    ]


def slide_metadata(source: Path) -> list[dict[str, object]]:
    with zipfile.ZipFile(source) as archive:
        present = set(archive.namelist())
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        rels = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
        targets = {
            relation.attrib.get("Id", ""): resolve_target(
                "ppt/presentation.xml", relation.attrib.get("Target", "")
            )
            for relation in rels
            if relation.attrib.get("Target")
        }
        slide_size = presentation.find(f"{{{P_NS}}}sldSz")
        width = int(slide_size.attrib.get("cx", "0")) if slide_size is not None else 0
        height = int(slide_size.attrib.get("cy", "0")) if slide_size is not None else 0
        result: list[dict[str, object]] = []
        for index, slide_id in enumerate(presentation.findall(f".//{{{P_NS}}}sldId"), 1):
            relationship_id = slide_id.attrib.get(f"{{{R_NS}}}id", "")
            part = targets.get(relationship_id)
            if not part or part not in present:
                continue
            slide = ET.fromstring(archive.read(part))
            relations = _part_relationships(archive, part)
            text_values = [
                value
                for node in slide.iter(f"{{{DRAWING_NS}}}t")
                if (value := (node.text or "").strip())
            ]
            text = " ".join(text_values)
            layout = next(
                (item["target"] for item in relations if item["type"] == SLIDE_LAYOUT_REL),
                None,
            )
            notes = next(
                (item["target"] for item in relations if item["type"] == NOTES_SLIDE_REL),
                None,
            )
            comments = [
                item["target"]
                for item in relations
                if item["type"].rsplit("/", 1)[-1] == "comments"
            ]
            comment_count = 0
            for comments_part in comments:
                if comments_part in present:
                    comments_root = ET.fromstring(archive.read(comments_part))
                    comment_count += sum(_local(node.tag) in {"cm", "comment"} for node in comments_root.iter())
            result.append(
                {
                    "index": index,
                    "name": Path(part).name,
                    "part": part,
                    "slide_id": slide_id.attrib.get("id", ""),
                    "relationship_id": relationship_id,
                    "hidden": slide.attrib.get("show", "1").casefold() in {"0", "false"},
                    "title": text_values[0][:160] if text_values else "",
                    "text_preview": text[:500],
                    "layout_part": layout,
                    "notes_part": notes,
                    "has_notes": notes is not None,
                    "comment_count": comment_count,
                    "chart_count": sum(item["type"] == CHART_REL for item in relations),
                    "width_emu": width,
                    "height_emu": height,
                }
            )
        return result


def _placeholder(size: tuple[int, int]):
    from PIL import Image, ImageDraw  # noqa: PLC0415

    image = Image.new("RGB", size, "#F0F0F0")
    draw = ImageDraw.Draw(image)
    width = max(3, min(size) // 80)
    draw.line(((0, 0), size), fill="#C8C8C8", width=width)
    draw.line(((0, size[1]), (size[0], 0)), fill="#C8C8C8", width=width)
    return image


def create_thumbnail_grids(
    source: Path,
    output_prefix: Path,
    cols: int = 3,
    rows: int = 4,
) -> dict:
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    if cols < 1 or rows < 1:
        raise ValueError("thumbnail rows and columns must be positive")
    metadata = slide_metadata(source)
    if not metadata:
        raise ValueError("presentation contains no registered slides")
    with tempfile.TemporaryDirectory(prefix="pptx-thumbnails-") as tmp:
        _, rendered, _ = render_pptx(source, Path(tmp), "slide", "png", 96)
        visible_count = sum(not bool(item["hidden"]) for item in metadata)
        rendered_hidden = len(rendered) == len(metadata) and visible_count != len(metadata)
        if len(rendered) not in {visible_count, len(metadata)}:
            raise ValueError(
                f"renderer produced {len(rendered)} page(s) for {visible_count} visible "
                f"slide(s) of {len(metadata)}; labels would be unreliable"
            )
        if not rendered and visible_count:
            raise ValueError("renderer produced no slide images")
        if rendered:
            with Image.open(rendered[0]) as sample:
                thumb_size = (320, round(320 * sample.height / sample.width))
        else:
            thumb_size = (320, 180)
        slides = []
        rendered_index = 0
        for item in metadata:
            hidden = bool(item["hidden"])
            label = str(item["name"]) + (" (hidden)" if hidden else "")
            if hidden and not rendered_hidden:
                slides.append((_placeholder(thumb_size), label))
            else:
                slides.append((rendered[rendered_index], label))
                rendered_index += 1

        output_prefix.parent.mkdir(parents=True, exist_ok=True)
        cells = cols * rows
        label_height = 28
        outputs = []
        for page_index, start in enumerate(range(0, len(slides), cells), 1):
            page_slides = slides[start : start + cells]
            grid_rows = (len(page_slides) + cols - 1) // cols
            grid = Image.new(
                "RGB",
                (cols * thumb_size[0], grid_rows * (thumb_size[1] + label_height)),
                "white",
            )
            draw = ImageDraw.Draw(grid)
            font = ImageFont.load_default()
            for index, (slide, label) in enumerate(page_slides):
                if isinstance(slide, Path):
                    with Image.open(slide) as opened:
                        image = opened.convert("RGB")
                else:
                    image = slide
                image.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                x = (index % cols) * thumb_size[0]
                y = (index // cols) * (thumb_size[1] + label_height)
                grid.paste(image, (x, y + label_height))
                draw.text((x + 8, y + 7), label, fill="black", font=font)
            output = (
                output_prefix.with_suffix(".jpg")
                if page_index == 1
                else output_prefix.with_name(f"{output_prefix.stem}-{page_index}").with_suffix(".jpg")
            )
            grid.save(output, quality=88)
            outputs.append(output)
    return {"metadata_version": 1, "outputs": outputs, "slides": metadata}
