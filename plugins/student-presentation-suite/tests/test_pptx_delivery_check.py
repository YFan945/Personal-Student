from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "student-presentation-ppt" / "scripts" / "pptx_delivery_check.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pptx_delivery_check", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PptxDeliveryCheckTests(unittest.TestCase):
    def write_minimal_pptx(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr(
                "ppt/slides/slide1.xml",
                """<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>""",
            )

    def write_valid_preview_and_manifest(self, pptx: Path, preview: Path, manifest: Path) -> None:
        image = Image.new("RGB", (640, 360), "white")
        image.paste("navy", (0, 0, 640, 80))
        image.save(preview)
        manifest.write_text(json.dumps({
            "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
            "slide_count": 1,
            "rendered_page_count": 1,
            "scenario_contract_passed": True,
            "preview_files": [preview.name],
            "preview_sha256": [hashlib.sha256(preview.read_bytes()).hexdigest()],
            "visual_inspection": {
                "completed": True, "inspected_pages": [1], "repair_cycles": 1,
                "remaining_blockers": 0,
            },
        }), encoding="utf-8")

    def test_derives_and_requires_notes_and_preview_by_default(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "demo-presentation.pptx"
            self.write_minimal_pptx(pptx)

            result = module.inspect_delivery(pptx, None, [])

        self.assertEqual(["notes", "preview"], result["missing_expected_files"])
        self.assertTrue(result["requirements"]["notes_required"])
        self.assertTrue(result["requirements"]["preview_required"])

    def test_explicit_exceptions_do_not_report_optional_files_missing(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "demo-presentation.pptx"
            self.write_minimal_pptx(pptx)

            result = module.inspect_delivery(
                pptx,
                None,
                [],
                require_notes=False,
                require_preview=False,
            )

        self.assertEqual([], result["missing_expected_files"])

    def test_font_inheritance_uncertainty_is_not_blocker_like(self) -> None:
        module = load_module()
        result = module.summarize_static_risks(
            {
                "findings": [
                    {
                        "slide": 1,
                        "shape": 1,
                        "text_preview": "Inherited text",
                        "char_count": 14,
                        "min_font_pt": None,
                        "risk": ["font-size-not-explicit"],
                    }
                ]
            }
        )

        self.assertEqual(0, result["blocker_like_count"])

    def test_qa_manifest_binds_current_pptx_and_decodable_preview(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, preview, manifest = root / "demo-presentation.pptx", root / "demo-preview.png", root / "qa-manifest.json"
            notes = root / "demo-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            self.write_valid_preview_and_manifest(pptx, preview, manifest)
            result = module.inspect_delivery(pptx, notes, [preview], qa_manifest=manifest)
        self.assertTrue(result["ok"])
        self.assertTrue(result["qa_manifest"]["valid"])
        self.assertEqual("complete", result["delivery_report"]["status"])
        self.assertEqual("1/1", result["delivery_report"]["preview_page_coverage"])

    def test_corrupt_preview_fails_qa_manifest(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, preview, manifest = root / "demo-presentation.pptx", root / "demo-preview.png", root / "qa-manifest.json"
            notes = root / "demo-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            preview.write_text("not an image", encoding="utf-8")
            manifest.write_text("{}", encoding="utf-8")
            result = module.inspect_delivery(pptx, notes, [preview], qa_manifest=manifest)
        self.assertFalse(result["ok"])
        self.assertFalse(result["preview_validation"][0]["valid"])
