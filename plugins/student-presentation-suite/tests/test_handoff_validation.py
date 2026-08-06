from __future__ import annotations

import unittest

from shared.handoff_validation import handoff_errors


class HandoffValidationTests(unittest.TestCase):
    def test_matching_handoff_passes(self) -> None:
        brief = {
            "topic": "AI literacy",
            "scenario": "coursework",
            "language": "Chinese",
            "duration_min": 5,
            "slide_count": 2,
            "audience": {"type": "teacher", "depth": "standard"},
            "controls": {
                "max_words_per_slide": 40,
                "speaker_notes": True,
                "citations": "classroom",
            },
            "deliverables": ["pptx", "preview"],
        }
        spec = {
            "meta": {
                "topic": "AI literacy",
                "scenario": "coursework",
                "language": "Chinese",
                "duration_min": 5,
                "slide_count": 2,
                "audience_type": "teacher",
                "audience_depth": "standard",
                "max_words_per_slide": 40,
                "include_speaker_notes": True,
                "citation_style": "classroom",
                "deliverables": ["preview", "pptx"],
            }
        }
        self.assertEqual([], handoff_errors(brief, spec))

    def test_mismatch_reports_exact_field(self) -> None:
        errors = handoff_errors(
            {"topic": "A", "deliverables": ["pptx"]},
            {"meta": {"topic": "B", "deliverables": ["pptx", "pdf"]}},
        )
        self.assertEqual({".meta.topic", ".meta.deliverables"}, {item["path"] for item in errors})
