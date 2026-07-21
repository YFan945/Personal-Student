#!/usr/bin/env python3
"""Static PPTX checks for student presentation review.

This script inspects PPTX XML and reports risk signals. It cannot prove true
rendered overflow or classroom readability; use its findings as review evidence.

Windows usage:
    python "${CLAUDE_PLUGIN_ROOT}/skills/student-presentation-review/scripts/pptx_static_check.py" deck.pptx --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


def inspect_pptx(path: Path) -> dict:
    from shared._import_helpers import load_inspect_pptx  # noqa: PLC0415
    return load_inspect_pptx(__file__)(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Static PPTX risk checker")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when the PPTX file is unreadable or corrupt (findings are warnings, not failures)",
    )
    args = parser.parse_args()

    result = inspect_pptx(args.pptx)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.strict and "error" in result:
            sys.exit(2)
    else:
        if "error" in result:
            print(result["note"])
            print(f"Error: {result['error']}")
            if args.strict:
                sys.exit(2)
            return
        print(result["note"])
        if not result["findings"]:
            print("No static risks found.")
            return
        for item in result["findings"]:
            print(
                f"Slide {item['slide']} shape {item['shape']}: "
                f"{', '.join(item['risk'])}; "
                f"min_font={item['min_font_pt']}; text={item['text_preview']!r}"
            )


if __name__ == "__main__":
    main()
