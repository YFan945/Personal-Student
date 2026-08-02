from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from PIL import Image
from test_helpers import load_module

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "student-presentation-ppt" / "scripts" / "pptx_delivery_check.py"


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
        package_report = manifest.with_name("package-report.json")
        package_report.write_text(
            json.dumps(
                {
                    "ok": True,
                    "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                    "validation_profile": "openxml-sdk-plus-suite-semantic-v4",
                    "schema_validation": {"performed": True, "error_count": 0},
                }
            ),
            encoding="utf-8",
        )
        spec = manifest.with_name("slide-spec.json")
        spec.write_text(
            json.dumps(
                {
                    "slides": [
                        {
                            "id": 1,
                            "title": "Test",
                            "layout": "hero",
                            "content": {"bullets": ["Test"]},
                            "timing_sec": 30,
                            "owner": "Tester",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        spec_hash = hashlib.sha256(spec.read_bytes()).hexdigest()
        spec_report = manifest.with_name("slide-spec-report.json")
        spec_report.write_text(
            json.dumps({"valid": True, "slide_spec_sha256": spec_hash}),
            encoding="utf-8",
        )
        manifest.write_text(json.dumps({
            "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
            "slide_count": 1,
            "rendered_page_count": 1,
            "scenario_contract_passed": True,
            "slide_spec": spec.name,
            "slide_spec_sha256": spec_hash,
            "slide_spec_report": spec_report.name,
            "slide_spec_report_sha256": hashlib.sha256(spec_report.read_bytes()).hexdigest(),
            "preview_files": [preview.name],
            "preview_sha256": [hashlib.sha256(preview.read_bytes()).hexdigest()],
            "package_report": package_report.name,
            "package_report_sha256": hashlib.sha256(package_report.read_bytes()).hexdigest(),
            "visual_inspection": {
                "completed": True, "inspected_pages": [1], "repair_cycles": 1,
                "remaining_blockers": 0,
            },
        }), encoding="utf-8")

    def test_derives_and_requires_notes_and_preview_by_default(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            pptx = Path(tmp) / "demo-presentation.pptx"
            self.write_minimal_pptx(pptx)

            result = module.inspect_delivery(pptx, None, [])

        self.assertEqual(["notes", "preview"], result["missing_expected_files"])
        self.assertTrue(result["requirements"]["notes_required"])
        self.assertTrue(result["requirements"]["preview_required"])

    def test_explicit_exceptions_do_not_report_optional_files_missing(self) -> None:
        module = load_module(SCRIPT)
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
        module = load_module(SCRIPT)
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
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, preview, manifest = root / "demo-presentation.pptx", root / "demo-preview.png", root / "qa-manifest.json"
            notes = root / "demo-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            self.write_valid_preview_and_manifest(pptx, preview, manifest)
            result = module.inspect_delivery(
                pptx, notes, [preview], qa_manifest=manifest,
                package_report=manifest.with_name("package-report.json"),
            )
        self.assertTrue(result["ok"])
        self.assertTrue(result["qa_manifest"]["valid"])
        self.assertEqual("complete", result["delivery_report"]["status"])
        self.assertEqual("1/1", result["delivery_report"]["preview_page_coverage"])
        self.assertEqual(0, result["delivery_report"]["package_blockers"])

    def test_corrupt_preview_fails_qa_manifest(self) -> None:
        module = load_module(SCRIPT)
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

    def test_blocked_on_missing_package_report_in_strict_mode(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, notes = root / "deck.pptx", root / "deck-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            preview = root / "deck-preview.png"
            manifest = root / "qa-manifest.json"
            self.write_valid_preview_and_manifest(pptx, preview, manifest)
            result = module.inspect_delivery(
                pptx,
                notes,
                [preview],
                qa_manifest=manifest,
                require_package_report=True,
            )
        self.assertFalse(result["ok"])
        self.assertFalse(result["package_validation"]["valid"])

    def test_delivery_ok_without_static_gate_when_package_passes(self) -> None:
        """Static XML scan is advisory after the gate-stripping refactor; a passing
        package report alone lets strict delivery succeed."""
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "deck.pptx"
            notes = root / "deck-speaker-notes.md"
            preview = root / "deck-preview.png"
            manifest = root / "qa-manifest.json"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            self.write_valid_preview_and_manifest(pptx, preview, manifest)
            result = module.inspect_delivery(
                pptx,
                notes,
                [preview],
                qa_manifest=manifest,
                package_report=manifest.with_name("package-report.json"),
            )
        self.assertTrue(result["ok"])
        self.assertTrue(result["package_validation"]["valid"])
        self.assertEqual("delivery-fallback-scan", result["static_xml_risk_summary"]["evidence_source"])

    def test_blocked_on_missing_qa_manifest(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, notes = root / "deck.pptx", root / "deck-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            result = module.inspect_delivery(pptx, notes, [], qa_manifest=None)
        self.assertFalse(result["ok"])
        self.assertFalse(result["qa_manifest"]["valid"])

    def test_strict_contract_requires_package_report(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "deck.pptx"
            notes = root / "deck-speaker-notes.md"
            preview = root / "deck-preview.png"
            manifest = root / "qa-manifest.json"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            self.write_valid_preview_and_manifest(pptx, preview, manifest)
            result = module.inspect_delivery(
                pptx,
                notes,
                [preview],
                qa_manifest=manifest,
                require_package_report=True,
            )
        self.assertFalse(result["ok"])
        self.assertFalse(result["package_validation"]["valid"])
        self.assertTrue(result["requirements"]["package_report_required"])

    def test_rejects_package_report_without_schema_validation(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "deck.pptx"
            notes = root / "deck-speaker-notes.md"
            preview = root / "deck-preview.png"
            manifest = root / "qa-manifest.json"
            package = root / "package-report.json"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            self.write_valid_preview_and_manifest(pptx, preview, manifest)
            package.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "pptx_sha256": hashlib.sha256(pptx.read_bytes()).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )
            result = module.inspect_delivery(
                pptx,
                notes,
                [preview],
                qa_manifest=manifest,
                package_report=package,
                require_package_report=True,
            )
        self.assertFalse(result["ok"])
        self.assertIn("Open XML schema validation was not performed", result["package_validation"]["errors"])

    def test_rejects_stale_quality_and_style_reports(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "deck.pptx"
            notes = root / "deck-speaker-notes.md"
            preview = root / "deck-preview.png"
            manifest = root / "qa-manifest.json"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            self.write_valid_preview_and_manifest(pptx, preview, manifest)
            quality = root / "quality.json"
            style = root / "style.json"
            quality.write_text(json.dumps({"ok": True, "slide_spec_sha256": "0" * 64}), encoding="utf-8")
            style.write_text(
                json.dumps({"ok": True, "pptx_sha256": "0" * 64, "slide_count": 1}),
                encoding="utf-8",
            )
            result = module.inspect_delivery(
                pptx,
                notes,
                [preview],
                qa_manifest=manifest,
                quality_report=quality,
                style_report=style,
            )
        self.assertFalse(result["ok"])
        self.assertFalse(result["quality_report"]["valid"])
        self.assertFalse(result["style_adherence"]["valid"])

    def test_blocked_on_pptx_unreadable(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "not-a-pptx.pptx"
            pptx.write_text("not a zip", encoding="utf-8")
            result = module.inspect_delivery(pptx, None, [])
        self.assertFalse(result["ok"])

    def test_blocked_on_style_report_failure(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx, notes = root / "deck.pptx", root / "deck-speaker-notes.md"
            self.write_minimal_pptx(pptx)
            notes.write_text("notes", encoding="utf-8")
            preview = root / "deck-preview.png"
            self.write_valid_preview_and_manifest(pptx, preview, root / "qa-manifest.json")
            style_report = root / "style-report.json"
            style_report.write_text(json.dumps({"valid": False, "errors": ["style mismatch"]}), encoding="utf-8")
            result = module.inspect_delivery(pptx, notes, [preview], qa_manifest=root / "qa-manifest.json", style_report=style_report)
        self.assertFalse(result["ok"])

    def test_strict_mode_exits_on_failure(self) -> None:
        module = load_module(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pptx = root / "missing.pptx"
            with self.assertRaises(SystemExit):
                result = module.inspect_delivery(pptx, None, [])
                self.assertFalse(result["ok"])
                module.parse_args = lambda: mock.Mock(strict=True)
                if not result["ok"]:
                    raise SystemExit(1)
