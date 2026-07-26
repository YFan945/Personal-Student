#!/usr/bin/env python3
"""Compile and gate a Slide Spec visual plan before PPTX generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.visual_plan import compile_visual_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a deterministic PPTX visual plan")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    raw = args.spec.read_bytes()
    try:
        text = raw.decode("utf-8")
        data = json.loads(text) if args.spec.suffix.casefold() == ".json" else yaml.safe_load(text)
    except (UnicodeDecodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise SystemExit(f"cannot read Slide Spec: {exc}") from exc
    result = compile_visual_plan(data if isinstance(data, dict) else {})
    result["slide_spec"] = str(args.spec.resolve())
    result["slide_spec_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Wrote visual plan: {args.output}")
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
