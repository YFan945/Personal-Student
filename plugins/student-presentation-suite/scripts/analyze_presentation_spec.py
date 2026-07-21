#!/usr/bin/env python3
"""Analyze a validated Slide Spec for story, evidence, density, and rehearsal risks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.presentation_quality import analyze_spec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze Student Presentation Slide Spec quality")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true", help="Fail on Critical or Major findings")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        raw = args.spec.read_text(encoding="utf-8")
        data = json.loads(raw) if args.spec.suffix.lower() == ".json" else yaml.safe_load(raw)
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2) from exc
    result = analyze_spec(data if isinstance(data, dict) else {})
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.json or not args.output:
        print(rendered)
    else:
        print(f"Wrote quality report: {args.output}")
    if args.strict and not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
