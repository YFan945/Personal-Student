"""Shared validation finding model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    code: str
    part: str
    detail: str
    severity: str = "error"
