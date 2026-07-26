"""PPTX-only runtime owned by student-presentation-suite."""

from .edit import add_slide, clean_package, delete_slide, reorder_slides
from .package import pack_directory, safe_extract_package
from .validate import validate_pptx

__all__ = [
    "add_slide",
    "clean_package",
    "delete_slide",
    "pack_directory",
    "reorder_slides",
    "safe_extract_package",
    "validate_pptx",
]
