from __future__ import annotations

import tempfile
import unittest
import zipfile
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import shared.pptx_static_core as core


def slide_xml(text: str, ph_type: str = "title", explicit_sz: str | None = None) -> str:
    rpr = f'<a:rPr sz="{explicit_sz}"/>' if explicit_sz else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="2" name="{ph_type} 1"/><p:nvPr><p:ph type="{ph_type}"/></p:nvPr></p:nvSpPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r>{rpr}<a:t>{text}</a:t></a:r></a:p></p:txBody>
    </p:sp>
  </p:spTree></p:cSld>
</p:sld>"""


def bounded_slide_xml(text: str, x: int, y: int, cx: int, cy: int, typeface: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="2" name="Body 1"/><p:nvPr><p:ph type="body"/></p:nvPr></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm></p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="2400"><a:latin typeface="{typeface}"/></a:rPr><a:t>{text}</a:t></a:r></a:p></p:txBody>
    </p:sp>
  </p:spTree></p:cSld>
</p:sld>"""


def rels_to_layout() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def rels_to_master() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


def style_xml(part: str, title_sz: str = "2800", body_sz: str = "2400") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<p:{part} xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree/></p:cSld>
  <p:txStyles>
    <a:titleStyle><a:lvl1pPr><a:defRPr sz="{title_sz}"/></a:lvl1pPr></a:titleStyle>
    <a:bodyStyle><a:lvl1pPr><a:defRPr sz="{body_sz}"/></a:lvl1pPr></a:bodyStyle>
  </p:txStyles>
</p:{part}>"""


class PptxStaticCoreTests(unittest.TestCase):
    def write_pptx(
        self,
        path: Path,
        slides: list[str],
        *,
        layout_title_sz: str | None = None,
        layout_body_sz: str | None = None,
        master_title_sz: str = "2800",
        master_body_sz: str = "2400",
    ) -> None:
        with zipfile.ZipFile(path, "w") as zf:
            for idx, slide in enumerate(slides, start=1):
                zf.writestr(f"ppt/slides/slide{idx}.xml", slide)
                zf.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", rels_to_layout())
            if layout_title_sz or layout_body_sz:
                zf.writestr(
                    "ppt/slideLayouts/slideLayout1.xml",
                    style_xml("sldLayout", layout_title_sz or "2800", layout_body_sz or "2400"),
                )
            else:
                zf.writestr(
                    "ppt/slideLayouts/slideLayout1.xml",
                    """<?xml version="1.0" encoding="UTF-8"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree/></p:cSld>
</p:sldLayout>""",
                )
            zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels_to_master())
            zf.writestr(
                "ppt/slideMasters/slideMaster1.xml",
                style_xml("sldMaster", master_title_sz, master_body_sz),
            )

    def test_resolves_master_title_font_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "master-title-size.pptx"
            self.write_pptx(pptx, [slide_xml("Inherited title")])

            result = core.inspect_pptx(pptx)

        self.assertNotIn("error", result)
        self.assertEqual(result["findings"], [])

    def test_caches_inherited_context_per_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "two-slides-one-layout.pptx"
            self.write_pptx(pptx, [slide_xml("First"), slide_xml("Second")])

            with mock.patch.object(
                core,
                "inherited_font_context_for_layout",
                wraps=core.inherited_font_context_for_layout,
            ) as wrapped:
                result = core.inspect_pptx(pptx)

        self.assertEqual(result["findings"], [])
        self.assertEqual(wrapped.call_count, 1)

    def test_resolves_layout_body_style_and_reports_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "layout-body-size.pptx"
            self.write_pptx(
                pptx,
                [slide_xml("Body text from layout", ph_type="body")],
                layout_body_sz="1800",
                master_body_sz="2600",
            )

            result = core.inspect_pptx(pptx)

        self.assertEqual(result["findings"][0]["min_font_pt"], 18)
        self.assertEqual(result["findings"][0]["font_size_source"], "layout-style")
        self.assertIn("font-size-below-20pt", result["findings"][0]["risk"])

    def test_explicit_font_size_overrides_inherited_style(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "explicit-size.pptx"
            self.write_pptx(
                pptx,
                [slide_xml("Explicit small title", explicit_sz="1800")],
                master_title_sz="3200",
            )

            result = core.inspect_pptx(pptx)

        self.assertEqual(result["findings"][0]["min_font_pt"], 18)
        self.assertEqual(result["findings"][0]["font_size_source"], "explicit")
        self.assertIn("heading-font-size-below-24pt", result["findings"][0]["risk"])

    def test_subtitle_below_24pt_is_not_treated_as_primary_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "subtitle-size.pptx"
            self.write_pptx(
                pptx,
                [slide_xml("Readable subtitle", ph_type="subTitle", explicit_sz="2200")],
            )

            result = core.inspect_pptx(pptx)

        risks = result["findings"][0]["risk"] if result["findings"] else []
        self.assertNotIn("heading-font-size-below-24pt", risks)

    def test_flags_outside_geometry_and_uncommon_font(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "geometry-font.pptx"
            self.write_pptx(
                pptx,
                [
                    bounded_slide_xml(
                        "Outside text",
                        x=12_000_000,
                        y=100_000,
                        cx=1_000_000,
                        cy=500_000,
                        typeface="Rare Decorative Font",
                    )
                ],
            )
            result = core.inspect_pptx(pptx)
        risks = set(result["findings"][0]["risk"])
        self.assertIn("shape-outside-slide", risks)
        self.assertIn("font-compatibility-review-required", risks)
        self.assertIn("Rare Decorative Font", result["font_families"])

    # ── Text overflow estimation ──────────────────────────────

    def test_cjk_overflow_detected_with_long_text(self) -> None:
        """长中文文本在小盒子里应检测到垂直溢出风险"""
        overflow = core.estimate_text_overflow(
            chars=120, is_cjk=True, font_size_pt=22,
            box_width_emu=int(10 * core.EMU_PER_CM),   # 10cm 宽
            box_height_emu=int(5 * core.EMU_PER_CM),    # 5cm 高
        )
        self.assertIsNotNone(overflow)
        # 22pt 中文: 字宽≈0.77cm, 10cm/0.77≈13 字/行, 120 字需 10 行
        # 行高≈1.09cm, 10 行≈10.9cm > 5cm → fill_ratio > 1.0
        self.assertGreater(overflow["fill_ratio"], 1.0)

    def test_cjk_text_fits_in_large_box(self) -> None:
        """短中文文本在大盒子里不应溢出"""
        overflow = core.estimate_text_overflow(
            chars=30, is_cjk=True, font_size_pt=22,
            box_width_emu=int(14 * core.EMU_PER_CM),   # 14cm 宽
            box_height_emu=int(8 * core.EMU_PER_CM),    # 8cm 高
        )
        self.assertIsNotNone(overflow)
        self.assertLess(overflow["fill_ratio"], 0.5)

    def test_english_overflow_detected(self) -> None:
        """长英文文本在小盒子里应检测到垂直溢出"""
        overflow = core.estimate_text_overflow(
            chars=200, is_cjk=False, font_size_pt=20,
            box_width_emu=int(10 * core.EMU_PER_CM),
            box_height_emu=int(4 * core.EMU_PER_CM),
        )
        self.assertIsNotNone(overflow)
        self.assertGreater(overflow["fill_ratio"], 0.85)

    def test_unknown_font_size_returns_none(self) -> None:
        """字号未知时无法估算"""
        overflow = core.estimate_text_overflow(
            chars=100, is_cjk=True, font_size_pt=None,
            box_width_emu=1_000_000, box_height_emu=1_000_000,
        )
        self.assertIsNone(overflow)

    def test_zero_dimensions_returns_none(self) -> None:
        """零尺寸文本框无法估算"""
        overflow = core.estimate_text_overflow(
            chars=50, is_cjk=True, font_size_pt=22,
            box_width_emu=0, box_height_emu=1_000_000,
        )
        self.assertIsNone(overflow)

    def test_very_short_text_never_overflows(self) -> None:
        """极短文本不应溢出"""
        overflow = core.estimate_text_overflow(
            chars=5, is_cjk=True, font_size_pt=22,
            box_width_emu=int(5 * core.EMU_PER_CM),
            box_height_emu=int(3 * core.EMU_PER_CM),
        )
        self.assertIsNotNone(overflow)
        self.assertLess(overflow["fill_ratio"], 0.85)

    def test_pptx_with_overflowing_cjk_text_is_flagged(self) -> None:
        """生成的 PPTX 中长文本应触发 text-vertical-overflow-risk"""
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "overflow.pptx"
            # ~100 中文字 + 24pt + 8cm×3cm 盒子 → 确定溢出
            # 24pt 字宽≈0.84cm, 8cm/0.84≈9 字/行, 100 字≈12 行
            # 行高≈1.19cm, 12 行≈14.3cm > 3cm → fill_ratio > 4.0
            chinese_text = (
                "人工智能技术正在深刻改变教育的面貌从个性化学习路径到智能评估系统"
                "自适应学习平台可以显著提升学生的学习效率和参与度"
            )
            self.write_pptx(
                pptx,
                [
                    bounded_slide_xml(
                        chinese_text,
                        x=500_000, y=1_500_000,
                        cx=int(8 * core.EMU_PER_CM),
                        cy=int(3 * core.EMU_PER_CM),
                        typeface="Microsoft YaHei",
                    )
                ],
            )
            result = core.inspect_pptx(pptx)
        risks = result["findings"][0]["risk"] if result["findings"] else []
        self.assertIn("text-vertical-overflow-risk", risks)
        self.assertIn("overflow_estimate", result["findings"][0])

    def test_pptx_with_short_text_no_overflow_flag(self) -> None:
        """短文本 PPTX 不应触发溢出风险"""
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "no-overflow.pptx"
            self.write_pptx(
                pptx,
                [
                    bounded_slide_xml(
                        "Short title here",
                        x=500_000, y=1_500_000,
                        cx=int(12 * core.EMU_PER_CM),
                        cy=int(7 * core.EMU_PER_CM),
                        typeface="Calibri",
                    )
                ],
            )
            result = core.inspect_pptx(pptx)
        risks = result["findings"][0]["risk"] if result["findings"] else []
        self.assertNotIn("text-vertical-overflow-risk", risks)


if __name__ == "__main__":
    unittest.main()
