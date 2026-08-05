"""Small shared helpers for the PPTX runtime package."""

from __future__ import annotations


def local(tag: str) -> str:
    """Return the local part of a Clark-notation element tag (``{ns}name`` -> ``name``)."""
    return tag.rsplit("}", 1)[-1]
