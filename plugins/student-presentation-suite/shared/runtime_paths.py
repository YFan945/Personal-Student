"""Runtime path discovery for the Claude Code plugin."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def project_root(env: dict[str, str] | None = None, cwd: Path | None = None) -> Path:
    values = env or os.environ
    configured = values.get("CLAUDE_PROJECT_DIR")
    if configured:
        resolved = Path(configured).expanduser().resolve()
        # 安全防护：拒绝路径穿越尝试
        if ".." in configured.split(os.sep):
            raise ValueError(
                f"CLAUDE_PROJECT_DIR 包含 '..' 路径穿越: {configured}"
            )
        return resolved
    return (cwd or Path.cwd()).resolve()


def output_root(
    requested: Path | None = None,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> Path:
    if requested:
        return requested.expanduser().resolve()
    return project_root(env=env, cwd=cwd) / "outputs"


def claude_config_root(env: dict[str, str] | None = None) -> Path:
    values = env or os.environ
    configured = values.get("CLAUDE_CONFIG_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / ".claude"


def installed_plugin_paths(
    plugin_id: str,
    env: dict[str, str] | None = None,
) -> list[Path]:
    config_root = claude_config_root(env)
    installed_path = config_root / "plugins" / "installed_plugins.json"
    if not installed_path.is_file():
        return []
    try:
        payload = json.loads(installed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    entries = payload.get("plugins", {}).get(plugin_id, [])
    paths: list[Path] = []
    for entry in entries:
        if isinstance(entry, dict) and entry.get("installPath"):
            path = Path(entry["installPath"]).expanduser().resolve()
            if path not in paths:
                paths.append(path)
    return paths


def document_skills_compatibility(
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    plugin_id = "document-skills@anthropic-agent-skills"
    required = ("SKILL.md", "pptxgenjs.md", "editing.md")
    candidates = installed_plugin_paths(plugin_id, env)
    for root in candidates:
        skill_root = root / "skills" / "pptx"
        missing = [name for name in required if not (skill_root / name).is_file()]
        if not missing:
            return {
                "ok": True,
                "plugin_id": plugin_id,
                "plugin_root": str(root),
                "skill_root": str(skill_root),
                "missing": [],
            }
    return {
        "ok": False,
        "plugin_id": plugin_id,
        "plugin_root": str(candidates[0]) if candidates else None,
        "skill_root": None,
        "missing": list(required),
        "detail": (
            "Install or update document-skills@anthropic-agent-skills; "
            "its pptx skill must include SKILL.md, pptxgenjs.md, and editing.md."
        ),
    }
