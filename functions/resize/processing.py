"""Image transformation used by the resize Cloud Function."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def resize_image(source_path: Path, destination_path: Path) -> tuple[int, int]:
    """Resize an image to half dimensions, preserving a one-pixel minimum."""

    with Image.open(source_path) as image:
        width, height = image.size
        dimensions = (max(1, width // 2), max(1, height // 2))
        image.resize(dimensions).save(destination_path)
    return dimensions
