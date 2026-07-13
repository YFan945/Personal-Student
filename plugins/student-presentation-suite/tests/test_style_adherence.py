from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from shared.style_adherence import inspect_style_adherence


class StyleAdherenceTests(unittest.TestCase):
    def test_flags_excess_unapproved_colors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "deck.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", """
                <p:sld xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'
                       xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'>
                  <p:cSld><p:spTree>
                    <p:sp><p:spPr><a:solidFill><a:srgbClr val='AA0000'/></a:solidFill></p:spPr></p:sp>
                    <p:sp><p:spPr><a:solidFill><a:srgbClr val='00AA00'/></a:solidFill></p:spPr></p:sp>
                    <p:sp><p:spPr><a:solidFill><a:srgbClr val='0000AA'/></a:solidFill></p:spPr></p:sp>
                  </p:spTree></p:cSld>
                </p:sld>""")
            report = inspect_style_adherence(pptx, "Modern Minimal")
        self.assertFalse(report["ok"])
        self.assertTrue(report["errors"])

    def test_flags_connector_width_outside_line_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "deck.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", """
                <p:sld xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'
                       xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'>
                  <p:cSld><p:spTree><p:cxnSp><p:spPr><a:ln w='38100'/></p:spPr></p:cxnSp></p:spTree></p:cSld>
                </p:sld>""")
            report = inspect_style_adherence(pptx, "Modern Minimal")
        self.assertFalse(report["ok"])
        self.assertIn("Connector widths", report["errors"][0])


if __name__ == "__main__":
    unittest.main()
