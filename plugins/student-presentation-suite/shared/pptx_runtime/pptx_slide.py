"""Find slide XML defects PowerPoint refuses to open, mirroring the official
pptx skill's denylist but checked directly on the XML tree instead of via
lxml schema-error messages (the suite uses the Open XML SDK for schema
validation).
"""

from __future__ import annotations

from defusedxml import ElementTree as ET

from .findings import Finding

SLIDE_PART_PREFIXES = (
    "ppt/slides/slide",
    "ppt/slideLayouts/slideLayout",
    "ppt/slideMasters/slideMaster",
    "ppt/notesSlides/notesSlide",
    "ppt/notesMasters/notesMaster",
    "ppt/handoutMasters/handoutMaster",
)

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"

_SRGB = f"{{{A_NS}}}srgbClr"
_TBLPR = f"{{{A_NS}}}tblPr"
_TABLE_STYLE_ID = f"{{{A_NS}}}tableStyleId"
_TXBODY = f"{{{P_NS}}}txBody"
_MITER = f"{{{A_NS}}}miter"
_ULN_TX = f"{{{A_NS}}}uLnTx"
_OVERRIDE_CLR_MAPPING = f"{{{P_NS}}}overrideClrMapping"
_NV_GRP_SP_PR = f"{{{P_NS}}}nvGrpSpPr"


def is_slide_part(part: str) -> bool:
    return any(part.startswith(prefix) for prefix in SLIDE_PART_PREFIXES)


def _six_hex(value: str) -> bool:
    if len(value) != 6:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value)


def fatal_slide_findings(part: str, root: ET.Element) -> list[Finding]:
    """Check the official denylist of slide XML defects PowerPoint refuses.

    Each check reports a specific, author-reparable defect; the fix belongs in
    the generator, not by hand-editing the packed XML.
    """
    findings: list[Finding] = []

    # Two <a:tableStyleId> in one <a:tblPr> (the schema allows one).
    for table_properties in root.iter(_TBLPR):
        style_ids = list(table_properties.iter(_TABLE_STYLE_ID))
        if len(style_ids) > 1:
            findings.append(
                Finding(
                    "fatal-slide-table-style-id",
                    part,
                    f"<a:tblPr> contains {len(style_ids)} <a:tableStyleId> (schema allows one)",
                )
            )

    # A colour that is not six hex digits.
    for srgb in root.iter(_SRGB):
        value = srgb.attrib.get("val", "")
        if not _six_hex(value):
            findings.append(
                Finding(
                    "fatal-slide-srgbclr",
                    part,
                    f"<a:srgbClr val=\"{value}\"> is not six hex digits",
                )
            )

    # A <p:txBody> with no children.
    for body in root.iter(_TXBODY):
        if len(body) == 0:
            findings.append(
                Finding("fatal-slide-txbody-empty", part, "<p:txBody> has no children")
            )

    # A line join with lim="NaN".
    for miter in root.iter(_MITER):
        if miter.attrib.get("lim") == "NaN":
            findings.append(
                Finding("fatal-slide-miter-nan", part, '<a:miter lim="NaN"> is invalid')
            )

    # <a:uLnTx> in a position the schema forbids (must be a direct child of <a:ln>).
    for node in root.iter(_ULN_TX):
        parent = _parent(root, node)
        parent_name = _local(parent.tag) if parent is not None else "?"
        if parent_name != "ln":
            findings.append(
                Finding(
                    "fatal-slide-ulntx",
                    part,
                    f"<a:uLnTx> is a child of <a:{parent_name}>, not <a:ln>",
                )
            )

    # <p:overrideClrMapping> in a position the schema forbids.
    for _node in root.iter(_OVERRIDE_CLR_MAPPING):
        findings.append(
            Finding(
                "fatal-slide-override-clr-mapping",
                part,
                "<p:overrideClrMapping> appears where the schema forbids it",
            )
        )

    # A <p:nvGrpSpPr> with no children.
    for group in root.iter(_NV_GRP_SP_PR):
        if len(group) == 0:
            findings.append(
                Finding("fatal-slide-nvgrpsppr-empty", part, "<p:nvGrpSpPr> has no children")
            )

    return findings


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parent(root: ET.Element, node: ET.Element) -> ET.Element | None:
    """Return the direct parent of ``node`` within ``root`` (or None)."""
    for candidate in root.iter():
        for child in candidate:
            if child is node:  # 身份比较：避免结构相同的兄弟节点被误判为父节点
                return candidate
    return None
