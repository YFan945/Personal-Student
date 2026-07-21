#!/usr/bin/env python3
"""Snapshot and restore Student Presentation deliverables without overwriting current files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def safe_child(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes output root: {candidate}") from exc
    return resolved


def snapshot(output_root: Path, revision_id: str, files: list[Path]) -> dict:
    output_root = output_root.resolve()
    version_root = safe_child(output_root, output_root / "versions" / revision_id)
    if version_root.exists():
        raise ValueError(f"Revision already exists: {revision_id}")
    version_root.mkdir(parents=True)
    entries = []
    for source in files:
        resolved = source.resolve()
        if not resolved.is_file():
            raise ValueError(f"Missing deliverable: {source}")
        try:
            rel_name = str(resolved.relative_to(output_root))
        except ValueError:
            rel_name = resolved.name
        target = version_root / rel_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resolved, target)
        entries.append(
            {
                "name": rel_name,
                "source": str(resolved),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "version_manifest": "1.0",
        "revision_id": revision_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": entries,
    }
    (version_root / "version-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"ok": True, "revision_root": str(version_root), "manifest": manifest}


def restore_candidate(output_root: Path, revision_id: str) -> dict:
    output_root = output_root.resolve()
    version_root = safe_child(output_root, output_root / "versions" / revision_id)
    manifest_path = version_root / "version-manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Unknown revision: {revision_id}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    restored_root = safe_child(output_root, output_root / "restored" / revision_id)
    if restored_root.exists():
        raise ValueError(f"Restore candidate already exists: {restored_root}")
    restored_root.mkdir(parents=True)
    restored = []
    for entry in manifest.get("files", []):
        source = safe_child(version_root, version_root / entry["name"])
        target = restored_root / entry["name"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        restored.append(str(target))
    return {
        "ok": True,
        "revision_id": revision_id,
        "restored_root": str(restored_root),
        "files": restored,
        "note": "Current deliverables were not overwritten. Review this candidate before activation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Student Presentation versions")
    sub = parser.add_subparsers(dest="action", required=True)
    save = sub.add_parser("snapshot")
    save.add_argument("--output-root", type=Path, required=True)
    save.add_argument("--revision-id", required=True)
    save.add_argument("--file", type=Path, action="append", required=True)
    restore = sub.add_parser("restore")
    restore.add_argument("--output-root", type=Path, required=True)
    restore.add_argument("--revision-id", required=True)
    args = parser.parse_args()
    try:
        result = (
            snapshot(args.output_root, args.revision_id, args.file)
            if args.action == "snapshot"
            else restore_candidate(args.output_root, args.revision_id)
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
