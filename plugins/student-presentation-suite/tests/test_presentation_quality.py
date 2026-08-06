from __future__ import annotations

import unittest

from shared.presentation_quality import analyze_spec


class PresentationQualityTests(unittest.TestCase):
    def complete_spec(self) -> dict:
        return {
            "meta": {
                "quality_level": "high-score",
                "max_words_per_slide": 40,
                "max_chinese_chars_per_slide": 80,
                "include_speaker_notes": True,
            },
            "evidence_ledger": [
                {
                    "id": "survey-1",
                    "title": "Class survey",
                    "source_type": "survey",
                    "locator": "survey.csv",
                    "confidence": "medium",
                    "used_on_slides": [1, 2],
                }
            ],
            "slides": [
                {
                    "id": 1,
                    "title": "一个具体问题打开汇报",
                    "kind": "content",
                    "role": "opening",
                    "claim": "现有流程让学生重复整理相同资料",
                    "content": "问题场景",
                    "slide_copy": "重复整理造成时间浪费",
                    "speaker_notes": "从课程项目中的一次返工说起。",
                    "evidence_refs": ["survey-1"],
                    "transition": "接下来用调研结果确认问题范围。",
                    "timing_sec": 30,
                    "owner": "Individual",
                },
                {
                    "id": 2,
                    "title": "62% 的同学经历过重复整理",
                    "kind": "content",
                    "role": "evidence",
                    "claim": "重复整理不是个别现象",
                    "content": "62%",
                    "slide_copy": "62% 的受访同学报告至少一次重复整理",
                    "speaker_notes": "说明样本与局限。",
                    "evidence_refs": ["survey-1"],
                    "transition": "因此方案重点是减少重复输入。",
                    "timing_sec": 45,
                    "owner": "Individual",
                },
                {
                    "id": 3,
                    "title": "结论与边界",
                    "kind": "closing",
                    "role": "limitation",
                    "claim": "方案只减少整理成本，不替代判断",
                    "content": "限制与下一步",
                    "slide_copy": "减少整理，不替代判断",
                    "speaker_notes": "总结并邀请提问。",
                    "timing_sec": 30,
                    "owner": "Individual",
                },
                {
                    "id": 4,
                    "title": "请老师提问",
                    "kind": "closing",
                    "role": "closing",
                    "content": "Q&A",
                    "timing_sec": 15,
                    "owner": "Individual",
                },
            ],
        }

    def test_complete_spec_has_no_major_findings(self) -> None:
        result = analyze_spec(self.complete_spec())
        self.assertEqual(0, result["summary"]["critical"])
        self.assertEqual(0, result["summary"]["major"])

    def test_detects_density_duplicate_generic_and_missing_evidence(self) -> None:
        data = self.complete_spec()
        data["slides"][1]["evidence_refs"] = []
        data["slides"][1]["slide_copy"] = (
            "在当今社会快速发展的背景下，" + "这是一段非常拥挤的页面文字" * 12 + "，因此效率提升 80%"
        )
        data["slides"][2] = {
            **data["slides"][1],
            "id": 3,
            "role": "conclusion",
            "evidence_refs": [],
        }
        result = analyze_spec(data)
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("chinese-density", codes)
        self.assertIn("generic-ai-wording", codes)
        self.assertIn("missing-evidence-reference", codes)
        self.assertIn("duplicate-slide", codes)

    def test_unknown_evidence_reference_is_critical(self) -> None:
        data = self.complete_spec()
        data["slides"][1]["evidence_refs"] = ["missing"]
        result = analyze_spec(data)
        self.assertEqual(1, result["summary"]["critical"])

    def test_content_layer_rules_are_minor_not_blocking(self) -> None:
        """每页证据引用 / 场景角色完整性 / opening / closing / limitation 均为 Minor，不阻断 --strict。"""
        data = {
            "meta": {
                "scenario": "defense",
                "quality_level": "high-score",
                "max_words_per_slide": 40,
                "max_chinese_chars_per_slide": 80,
                "include_speaker_notes": True,
            },
            "slides": [
                {
                    "id": 1,
                    "kind": "content",
                    "role": "method",
                    "title": "方法页 80% 提升",
                    "claim": "方法 X 提升效率",
                    "content": "80%",
                    "slide_copy": "该方法提升 80% 效率，因此成本下降",
                    "timing_sec": 30,
                    "owner": "Individual",
                }
            ],
        }
        result = analyze_spec(data)
        by_code = {item["code"]: item["severity"] for item in result["findings"]}
        for code in (
            "missing-evidence-reference",
            "missing-opening-hook",
            "missing-closing",
            "missing-limitation",
            "missing-story-role",
        ):
            self.assertEqual("Minor", by_code.get(code), f"{code} should be Minor, got {by_code.get(code)}")
        self.assertEqual(0, result["summary"]["critical"])
        self.assertEqual(0, result["summary"]["major"])


if __name__ == "__main__":
    unittest.main()
