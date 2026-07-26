"""Runtime path discovery for the Claude Code plugin."""

from __future__ import annotations

import os
from pathlib import Path

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


def get_pptx_runtime_root() -> Path:
    """返回 suite-owned PPTX runtime package 路径。"""
    return PLUGIN_ROOT / "shared" / "pptx_runtime"
