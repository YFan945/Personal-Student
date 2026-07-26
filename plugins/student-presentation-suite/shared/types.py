"""类型定义（TypedDict / dataclass）用于结构化数据传递。

这些类型旨在逐步替代 ``dict[str, Any]``，在不破坏现有 API
的情况下为共享模块提供静态类型检查支持。
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

# ---------------------------------------------------------------------------
# Presentation Brief
# ---------------------------------------------------------------------------


class BriefMeta(TypedDict):
    """Presentation Brief 元数据字段。"""

    topic: str
    scenario: str
    presentation_type: str
    language: str
    visual_style: NotRequired[str]
    slide_count: int
    max_words_per_slide: NotRequired[int]
    max_chinese_chars_per_slide: NotRequired[int]
    include_speaker_notes: NotRequired[bool]
    output_prefix: NotRequired[str]


class BriefContentSlide(TypedDict):
    """Brief 中的单个幻灯片定义。"""

    id: int
    title: str
    kind: str
    layout: str
    content: dict[str, Any]
    notes: NotRequired[str]
    evidence_ids: NotRequired[list[str]]


class PresentationBrief(TypedDict):
    """完整的 Presentation Brief 文档。"""

    meta: BriefMeta
    slides: list[BriefContentSlide]
    evidence_ledger: NotRequired[list[dict[str, Any]]]


# ---------------------------------------------------------------------------
# Slide Spec
# ---------------------------------------------------------------------------


class SlideSpecMeta(TypedDict):
    """Slide Spec 元数据字段。"""

    topic: str
    presentation_type: str
    scenario: NotRequired[str]
    language: str
    slide_count: int
    visual_style: NotRequired[str]
    output_prefix: NotRequired[str]
    max_words_per_slide: NotRequired[int]
    max_chinese_chars_per_slide: NotRequired[int]
    include_speaker_notes: NotRequired[bool]


class Slide(TypedDict):
    """Slide Spec 中的单个幻灯片。"""

    id: int
    title: str
    kind: str
    layout: str
    content: dict[str, Any]
    notes: NotRequired[str]
    roles: NotRequired[list[str]]
    evidence_ids: NotRequired[list[str]]


class SlideSpec(TypedDict):
    """完整的 Slide Spec 文档。"""

    meta: SlideSpecMeta
    slides: list[Slide]
    evidence_ledger: NotRequired[list[dict[str, Any]]]


# ---------------------------------------------------------------------------
# Design Tokens
# ---------------------------------------------------------------------------


class TokenPalette(TypedDict):
    """Design token 调色板。"""

    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    divider: str


class TokenTypography(TypedDict):
    """Design token 字体配置。"""

    font_family: str
    title_size: float
    body_size: float
    line_height: float
    cjk_font_family: NotRequired[str]


class TokenGeometry(TypedDict):
    """Design token 间距与几何。"""

    slide_width: float
    slide_height: float
    content_margin: float
    section_padding: float
    corner_radius: NotRequired[float]


class DesignTokens(TypedDict):
    """完整的视觉设计标记。"""

    name: str
    palette: TokenPalette
    typography: TokenTypography
    geometry: TokenGeometry
    lines: dict[str, Any]


# ---------------------------------------------------------------------------
# QA / Delivery
# ---------------------------------------------------------------------------


class QaManifest(TypedDict):
    """QA 验证清单。"""

    pptx_sha256: str
    slide_count: int
    rendered_page_count: int
    scenario_contract_passed: NotRequired[bool]
    slide_spec_sha256: NotRequired[str]
    slide_spec_report: NotRequired[str]
    slide_spec_report_sha256: NotRequired[str]
    visual_plan: NotRequired[str]
    visual_plan_sha256: NotRequired[str]
    preview_files: NotRequired[list[str]]
    preview_sha256: NotRequired[list[str]]
    visual_inspection: NotRequired[dict[str, Any]]


class DeliveryReport(TypedDict):
    """交付检查报告摘要。"""

    ok: bool
    status: str
    slide_count: int | None
    static_blockers: int | None
    render_blockers: int
    style_adherence_passed: bool | None
    preview_page_coverage: str
    repair_cycles: int | None
