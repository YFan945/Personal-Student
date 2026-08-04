#!/usr/bin/env python3
"""Compare two Slide Specs and emit a lock-aware revision manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _yaml() -> Any:
    """Lazily import PyYAML with a friendly message when missing."""
    try:
        import yaml
    except ImportError:
        print(
            "Missing dependency. Install plugin validation dependencies with: "
            "python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        raise SystemExit(3) from None
    return yaml


def load(path: Path) -> dict[str, Any]:
    yaml_mod = _yaml()
    raw = path.read_text(encoding="utf-8")
    value = json.loads(raw) if path.suffix.lower() == ".json" else yaml_mod.safe_load(raw)
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slides_by_id(data: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        int(slide["id"]): slide
        for slide in data.get("slides", [])
        if isinstance(slide, dict) and isinstance(slide.get("id"), int)
    }


def build_manifest(old_path: Path, new_path: Path, reason: str) -> dict[str, Any]:
    old = load(old_path)
    new = load(new_path)
    old_slides = slides_by_id(old)
    new_slides = slides_by_id(new)
    changed: list[int] = []
    preserved_locked: list[int] = []
    violations: list[dict[str, Any]] = []
    for slide_id in sorted(set(old_slides) | set(new_slides)):
        before = old_slides.get(slide_id)
        after = new_slides.get(slide_id)
        if before != after:
            changed.append(slide_id)
            if before and before.get("locked"):
                violations.append(
                    {
                        "slide": slide_id,
                        "problem": "Locked slide changed or was removed.",
                        "lock_reason": before.get("lock_reason"),
                    }
                )
        elif before and before.get("locked"):
            preserved_locked.append(slide_id)
    target_slides = set(new.get("target_slides") or [])
    operation = new.get("revision_operation")
    if target_slides:
        for slide_id in changed:
            if slide_id not in target_slides:
                violations.append(
                    {
                        "slide": slide_id,
                        "problem": "Slide changed outside the declared revision scope.",
                        "revision_operation": operation,
                    }
                )
    old_revision = old.get("revision") or {}
    new_revision = new.get("revision") or {}
    return {
        "manifest_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),  # noqa: UP017  # 环境无 datetime.UTC
        "parent_revision": old_revision.get("revision_id") or old_path.stem,
        "revision_id": new_revision.get("revision_id") or new_path.stem,
        "reason": reason,
        "revision_operation": operation,
        "target_slides": sorted(target_slides),
        "old_file": str(old_path.resolve()),
        "new_file": str(new_path.resolve()),
        "old_sha256": digest(old_path),
        "new_sha256": digest(new_path),
        "changed_slides": changed,
        "preserved_locked_slides": preserved_locked,
        "violations": violations,
        "lock_violations": [
            item for item in violations if "Locked slide" in item.get("problem", "")
        ],
        "valid": not violations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Slide Spec revision manifest")
    parser.add_argument("old_spec", type=Path)
    parser.add_argument("new_spec", type=Path)
    parser.add_argument("--reason", default="user-requested revision")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    yaml_mod = _yaml()
    try:
        manifest = build_manifest(args.old_spec, args.new_spec, args.reason)
    except (OSError, ValueError, yaml_mod.YAMLError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2) from exc
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.strict and not manifest["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
