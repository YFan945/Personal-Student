from __future__ import annotations

import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from shared.pptx_runtime.charts import validate_charts
from shared.pptx_runtime.edit import clean_package
from shared.pptx_runtime.normalize import normalize_unpacked
from shared.pptx_runtime.package import pack_directory, safe_extract_package
from shared.pptx_runtime.render import align_rendered_pages
from shared.pptx_runtime.soffice import build_socket_shim, soffice_environment
from shared.pptx_runtime.validate import _validate_master_themes


def write_clean_fixture(root: Path, dangling: bool = False) -> bytes:
    content_types = (
        b'<?xml version="1.0"?><Types '
        b'xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        b'<Default Extension="xml" ContentType="application/xml"/>'
        b"<Override PartName='/orphan/a.xml' ContentType='application/xml'/>"
        b"<Override PartName='/orphan/b.xml' ContentType='application/xml'/>"
        b"</Types>"
    )
    parts = {
        "[Content_Types].xml": content_types,
        "_rels/.rels": (
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Target="ppt/presentation.xml"/>'
            b"</Relationships>"
        ),
        "ppt/presentation.xml": (
            b'<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            b'<p:sldIdLst><p:sldId id="256" r:id="rIdSlide"/></p:sldIdLst>'
            b"</p:presentation>"
        ),
        "ppt/_rels/presentation.xml.rels": (
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rIdSlide" '
            b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
            b'Target="slides/slide1.xml"/>'
            b"</Relationships>"
        ),
        "ppt/slides/slide1.xml": b"<slide/>",
        "orphan/a.xml": b"<orphan/>",
        "orphan/b.xml": b"<orphan/>",
    }
    if dangling:
        parts["ppt/slides/_rels/slide1.xml.rels"] = (
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Target="slides/missing.xml"/>'
            b"</Relationships>"
        )
    for name, payload in parts.items():
        path = root / Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return content_types


class PackageSafetyTests(unittest.TestCase):
    def test_extract_rejects_excessive_compression_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "bomb.pptx"
            with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("large.xml", b"0" * 4096)
            with (
                mock.patch("shared.pptx_runtime.package.COMPRESSION_RATIO_MIN_BYTES", 1),
                mock.patch("shared.pptx_runtime.package.MAX_COMPRESSION_RATIO", 2),
            ):
                with self.assertRaisesRegex(ValueError, "compression-ratio"):
                    safe_extract_package(source, root / "output")

    def test_pack_rejects_excessive_member_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unpacked = root / "unpacked"
            unpacked.mkdir()
            (unpacked / "one.xml").write_text("<one/>", encoding="utf-8")
            (unpacked / "two.xml").write_text("<two/>", encoding="utf-8")
            with mock.patch("shared.pptx_runtime.package.MAX_PACKAGE_MEMBERS", 1):
                with self.assertRaisesRegex(ValueError, "too many members"):
                    pack_directory(unpacked, root / "output.pptx")


class GeneratedPackageNormalizationTests(unittest.TestCase):
    def test_removes_only_undeclared_chart_axis_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chart_path = root / "ppt" / "charts" / "chart1.xml"
            chart_path.parent.mkdir(parents=True)
            chart_path.write_text(
                (
                    '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">'
                    "<c:chart><c:plotArea><c:barChart>"
                    '<c:axId val="1"/><c:axId val="2"/><c:axId val="3"/>'
                    "</c:barChart>"
                    '<c:catAx><c:axId val="1"/></c:catAx>'
                    '<c:valAx><c:axId val="2"/></c:valAx>'
                    "</c:plotArea></c:chart></c:chartSpace>"
                ),
                encoding="utf-8",
            )
            changed = normalize_unpacked(root)
            normalized = chart_path.read_text(encoding="utf-8")
        self.assertEqual(["ppt/charts/chart1.xml"], changed)
        self.assertIn('val="1"', normalized)
        self.assertIn('val="2"', normalized)
        self.assertNotIn('val="3"', normalized)


class CleanPackageTests(unittest.TestCase):
    def test_clean_removes_only_unreachable_parts_and_single_quote_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_clean_fixture(root)
            removed = clean_package(root)
            types = (root / "[Content_Types].xml").read_text(encoding="utf-8")
            self.assertEqual(["orphan/a.xml", "orphan/b.xml"], removed)
            self.assertFalse((root / "orphan").exists())
            self.assertNotIn("/orphan/", types)
            self.assertTrue((root / "ppt" / "presentation.xml").is_file())

    def test_clean_refuses_dangling_relationship_without_deleting_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original_types = write_clean_fixture(root, dangling=True)
            with self.assertRaisesRegex(ValueError, "dangling relationship"):
                clean_package(root)
            self.assertTrue((root / "orphan" / "a.xml").is_file())
            self.assertEqual(original_types, (root / "[Content_Types].xml").read_bytes())

    def test_clean_rolls_back_when_move_fails_mid_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"
            root.mkdir()
            original_types = write_clean_fixture(root)
            real_move = shutil.move
            calls = 0

            def fail_second_move(source: str, destination: str):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected move failure")
                return real_move(source, destination)

            with mock.patch("shared.pptx_runtime.edit.shutil.move", side_effect=fail_second_move):
                with self.assertRaisesRegex(OSError, "injected move failure"):
                    clean_package(root)
            self.assertTrue((root / "orphan" / "a.xml").is_file())
            self.assertTrue((root / "orphan" / "b.xml").is_file())
            self.assertEqual(original_types, (root / "[Content_Types].xml").read_bytes())


class ChartValidationTests(unittest.TestCase):
    def test_chart_validator_reports_axis_series_and_extension_structure(self) -> None:
        chart = """<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
          <c:chart><c:plotArea><c:barChart>
            <c:ser><c:idx val="0"/><c:order val="0"/></c:ser>
            <c:ser><c:idx val="0"/><c:order val="0"/></c:ser>
            <c:axId val="10"/>
          </c:barChart>
          <c:catAx><c:axId val="10"/><c:crossAx val="20"/></c:catAx>
          <c:valAx><c:axId val="20"/><c:crossAx val="30"/><c:extLst/><c:delete val="0"/></c:valAx>
          <c:valAx><c:axId val="30"/><c:crossAx val="20"/></c:valAx>
          </c:plotArea></c:chart>
        </c:chartSpace>"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "ppt" / "charts" / "chart1.xml"
            path.parent.mkdir(parents=True)
            path.write_text(chart, encoding="utf-8")
            findings = []
            validate_charts(root, {"ppt/charts/chart1.xml"}, findings)
        codes = {finding.code for finding in findings}
        self.assertIn("chart-axis-cardinality", codes)
        self.assertIn("chart-series-idx", codes)
        self.assertIn("chart-series-order", codes)
        self.assertIn("chart-axis-cross-nonreciprocal", codes)
        self.assertIn("chart-ext-list-order", codes)

    def test_chart_validator_allows_sparse_cache_but_reports_other_damage(self) -> None:
        chart = """<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
          <c:chart><c:plotArea><c:lineChart><c:ser><c:idx val="0"/><c:order val="0"/>
            <c:cat><c:strRef><c:f>'Data'!$A$1:$A$3</c:f><c:strCache><c:ptCount val="2"/><c:pt idx="0"><c:v>A</c:v></c:pt><c:pt idx="0"><c:v>B</c:v></c:pt></c:strCache></c:strRef></c:cat>
            <c:val><c:numRef><c:f>'Data'!$B$1:$B$4</c:f><c:numCache><c:ptCount val="4"/><c:pt idx="0"><c:v>1</c:v></c:pt><c:pt idx="1"><c:v>bad</c:v></c:pt></c:numCache></c:numRef></c:val>
            <c:axId val="10"/><c:axId val="20"/>
          </c:ser></c:lineChart></c:plotArea></c:chart>
        </c:chartSpace>"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "ppt" / "charts" / "chart1.xml"
            path.parent.mkdir(parents=True)
            path.write_text(chart, encoding="utf-8")
            findings = []
            validate_charts(root, {"ppt/charts/chart1.xml"}, findings)
        codes = {finding.code for finding in findings}
        self.assertNotIn("chart-cache-count", codes)
        self.assertIn("chart-cache-index", codes)
        self.assertIn("chart-cache-number", codes)
        self.assertIn("chart-formula-cache-count", codes)
        self.assertIn("chart-series-cardinality", codes)

    def test_chart_validator_checks_embedded_workbook_and_formula_sheet(self) -> None:
        chart = """<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <c:chart><c:plotArea><c:lineChart><c:ser><c:idx val="0"/><c:order val="0"/>
          <c:val><c:numRef><c:f>'Missing'!$A$1</c:f><c:numCache><c:ptCount val="1"/><c:pt idx="0"><c:v>1</c:v></c:pt></c:numCache></c:numRef></c:val>
          <c:axId val="10"/><c:axId val="20"/></c:ser></c:lineChart></c:plotArea></c:chart>
          <c:externalData r:id="rId1"/></c:chartSpace>"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chart_path = root / "ppt" / "charts" / "chart1.xml"
            rels_path = root / "ppt" / "charts" / "_rels" / "chart1.xml.rels"
            workbook_path = root / "ppt" / "embeddings" / "data.xlsx"
            chart_path.parent.mkdir(parents=True)
            rels_path.parent.mkdir(parents=True)
            workbook_path.parent.mkdir(parents=True)
            chart_path.write_text(chart, encoding="utf-8")
            rels_path.write_text(
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/package" Target="../embeddings/data.xlsx"/></Relationships>',
                encoding="utf-8",
            )
            with zipfile.ZipFile(workbook_path, "w") as workbook:
                workbook.writestr(
                    "xl/workbook.xml",
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>',
                )
                workbook.writestr(
                    "xl/_rels/workbook.xml.rels",
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
                )
            files = {
                "ppt/charts/chart1.xml",
                "ppt/charts/_rels/chart1.xml.rels",
                "ppt/embeddings/data.xlsx",
            }
            findings = []
            validate_charts(root, files, findings)
        self.assertIn("chart-formula-sheet-missing", {finding.code for finding in findings})


class SharedAssetRiskTests(unittest.TestCase):
    def test_reports_shared_slide_master_as_info(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parts = {
                "ppt/slides/_rels/slide1.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>',
                "ppt/slides/_rels/slide2.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>',
                "ppt/slideLayouts/_rels/slideLayout1.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>',
            }
            files = {
                "ppt/presentation.xml",
                "ppt/slides/slide1.xml",
                "ppt/slides/slide2.xml",
                "ppt/slideLayouts/slideLayout1.xml",
                "ppt/slideMasters/slideMaster1.xml",
                *parts,
            }
            for name in files:
                path = root / Path(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(parts.get(name, "<root/>"), encoding="utf-8")
            findings = []
            _validate_master_themes(root, files, findings)
        risks = [finding for finding in findings if finding.code == "shared-slide-master"]
        self.assertEqual(1, len(risks))
        self.assertEqual("info", risks[0].severity)
        self.assertIn("2 slides", risks[0].detail)


class RenderAlignmentTests(unittest.TestCase):
    def test_hidden_slide_placeholder_restores_original_order(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "preview-1.png"
            third = root / "preview-2.png"
            Image.new("RGB", (320, 180), "red").save(first)
            Image.new("RGB", (320, 180), "blue").save(third)
            metadata = [
                {"hidden": False, "width_emu": 0, "height_emu": 0},
                {"hidden": True, "width_emu": 0, "height_emu": 0},
                {"hidden": False, "width_emu": 0, "height_emu": 0},
            ]
            pages, placeholders = align_rendered_pages(
                [first, third], metadata, root, "preview", "png"
            )
            colors = [Image.open(page).getpixel((160, 90)) for page in pages]
        self.assertEqual([2], placeholders)
        self.assertEqual((255, 0, 0), colors[0])
        self.assertEqual((0, 0, 255), colors[2])
        self.assertNotEqual(colors[0], colors[1])


class SofficeSandboxTests(unittest.TestCase):
    def test_environment_loads_hashed_shim_only_when_linux_af_unix_is_blocked(self) -> None:
        shim = Path("/tmp/lo-socket-shim-test.so")
        with (
            mock.patch("shared.pptx_runtime.soffice.platform.system", return_value="Linux"),
            mock.patch("shared.pptx_runtime.soffice.af_unix_available", return_value=False),
            mock.patch("shared.pptx_runtime.soffice.build_socket_shim", return_value=shim),
            mock.patch.dict(os.environ, {"LD_PRELOAD": "/existing.so"}, clear=False),
        ):
            environment, messages = soffice_environment()
        self.assertEqual(f"{shim}{os.pathsep}/existing.so", environment["LD_PRELOAD"])
        self.assertIn("AF_UNIX blocked", messages[0])

    def test_environment_can_force_real_denial_path_for_linux_ci(self) -> None:
        shim = Path("/tmp/lo-socket-shim-test.so")
        with (
            mock.patch("shared.pptx_runtime.soffice.platform.system", return_value="Linux"),
            mock.patch("shared.pptx_runtime.soffice.af_unix_available", return_value=True),
            mock.patch("shared.pptx_runtime.soffice.build_socket_shim", return_value=shim),
            mock.patch.dict(os.environ, {"PPTX_RUNTIME_FORCE_AF_UNIX_SHIM": "1"}, clear=True),
        ):
            environment, messages = soffice_environment()
        self.assertEqual("1", environment["PPTX_RUNTIME_TEST_DENY_AF_UNIX"])
        self.assertEqual(str(shim), environment["LD_PRELOAD"])
        self.assertIn("denial simulation", messages[0])

    @unittest.skipUnless(os.name == "posix" and shutil.which("cc"), "Linux C compiler required")
    def test_socket_shim_compiles(self) -> None:
        self.assertTrue(build_socket_shim().is_file())


if __name__ == "__main__":
    unittest.main()
