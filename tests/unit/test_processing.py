from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from processing import resize_image


@pytest.mark.parametrize(
    ("source_dimensions", "expected_dimensions", "name"),
    [
        ((1600, 1000), (800, 500), "landscape.jpg"),
        ((641, 481), (320, 240), "odd.png"),
        ((1, 1), (1, 1), "tiny.png"),
    ],
)
def test_resize_image_preserves_nonzero_half_dimensions(
    tmp_path: Path,
    source_dimensions: tuple[int, int],
    expected_dimensions: tuple[int, int],
    name: str,
) -> None:
    source = tmp_path / name
    output = tmp_path / f"resized-{name}"
    Image.new("RGB", source_dimensions, color="blue").save(source)

    assert resize_image(source, output) == expected_dimensions
    with Image.open(output) as image:
        assert image.size == expected_dimensions


def test_resize_image_rejects_non_image_data(tmp_path: Path) -> None:
    source = tmp_path / "invalid.bin"
    source.write_bytes(b"not an image")

    with pytest.raises(Exception):
        resize_image(source, tmp_path / "output.bin")
