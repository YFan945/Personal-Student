#!/usr/bin/env python3
"""Create a machine-readable style-adherence report for a PPTX delivery."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.style_adherence import inspect_style_adherence


def main() -> None:
    parser = argparse.ArgumentParser(description="Check PPTX adherence to resolved design tokens")
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--visual-style", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = inspect_style_adherence(args.pptx, args.visual_style)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if args.strict and not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
