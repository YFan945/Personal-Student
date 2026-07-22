"""Helpers for importing shared modules from plugin-root-relative paths."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


@contextmanager
def _plugin_root_on_path(plugin_root: Path) -> Generator[None, None, None]:
    """Temporarily add ``plugin_root`` to ``sys.path`` inside the context.

    Restores ``sys.path`` to its original state on exit, even if an
    exception occurs inside the context.
    """
    root_str = str(plugin_root)
    added = root_str not in sys.path
    if added:
        sys.path.insert(0, root_str)
    try:
        yield
    finally:
        if added:
            try:
                sys.path.remove(root_str)
            except ValueError:
                pass


def load_inspect_pptx(script_path: str | Path) -> type:
    """Import and return the shared ``inspect_pptx`` function.

    Temporarily adds the plugin root to ``sys.path`` to resolve the
    ``shared`` package.  Safe to call multiple times — repeated calls
    are cached by the import system.
    """
    plugin_root = Path(script_path).resolve().parents[3]
    with _plugin_root_on_path(plugin_root):
        from shared import inspect_pptx
    return inspect_pptx
