"""Background-aware descriptor helpers.

Two complementary strategies reduce the influence of a uniform background on
colour and texture descriptors:

* ``block_variance_weights`` weights a fixed grid by local variance, so flat
  regions (sky, foliage, walls) contribute less than structured ones.
* ``object_mask`` isolates the foreground when the image actually has a
  separable background, measured by ``separability_ratio``.

The decision is taken per image from pixel statistics only. Dataset labels are
never used, so the same rule applies to user uploads.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from PIL import Image

BORDER_FRACTION = 0.15
CENTER_FRACTION = 0.25
DEFAULT_GRID = 4
DEFAULT_THRESHOLD = 1.2


def _rgb_array(image: Image.Image) -> NDArray[np.float32]:
    return np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0


def _border_pixels(rgb: NDArray[np.float32]) -> NDArray[np.float32]:
    height, width, _ = rgb.shape
    margin_y = max(1, int(height * BORDER_FRACTION))
    margin_x = max(1, int(width * BORDER_FRACTION))
    return np.concatenate(
        (
            rgb[:margin_y].reshape(-1, 3),
            rgb[-margin_y:].reshape(-1, 3),
            rgb[:, :margin_x].reshape(-1, 3),
            rgb[:, -margin_x:].reshape(-1, 3),
        )
    )


def _center_pixels(rgb: NDArray[np.float32]) -> NDArray[np.float32]:
    height, width, _ = rgb.shape
    top = int(height * CENTER_FRACTION)
    left = int(width * CENTER_FRACTION)
    bottom = max(top + 1, height - top)
    right = max(left + 1, width - left)
    return rgb[top:bottom, left:right].reshape(-1, 3)


def separability_ratio(image: Image.Image) -> float:
    """Return how much the centre differs from the border, in border-noise units.

    A large ratio means the image has a distinct background that can be
    removed. A ratio near or below 1 means the border is as varied as the
    centre, so the whole image carries the information.
    """
    rgb = _rgb_array(image)
    border = _border_pixels(rgb)
    center = _center_pixels(rgb)
    border_std = float(border.std(axis=0).mean())
    gap = float(np.linalg.norm(border.mean(axis=0) - center.mean(axis=0)))
    return gap / max(border_std, 1e-6)


def block_variance_weights(
    image: Image.Image,
    grid: int = DEFAULT_GRID,
) -> NDArray[np.float32]:
    """Return a ``grid × grid`` weight map normalised to sum to 1.

    Flat blocks receive a small weight, structured blocks a large one. A
    uniform image falls back to equal weights so the descriptors stay stable.
    """
    if grid < 1:
        raise ValueError("La grille de blocs doit être au moins de 1.")
    rgb = _rgb_array(image)
    height, width, _ = rgb.shape
    weights = np.zeros((grid, grid), dtype=np.float64)
    for row in range(grid):
        top = (height * row) // grid
        bottom = max(top + 1, (height * (row + 1)) // grid)
        for column in range(grid):
            left = (width * column) // grid
            right = max(left + 1, (width * (column + 1)) // grid)
            block = rgb[top:bottom, left:right]
            weights[row, column] = float(block.std(axis=(0, 1)).mean())

    weights += 1e-6
    total = weights.sum()
    if not np.isfinite(total) or total <= 0:
        return np.full((grid, grid), 1.0 / (grid * grid), dtype=np.float32)
    return (weights / total).astype(np.float32)


def object_mask(
    image: Image.Image,
    threshold: float = DEFAULT_THRESHOLD,
) -> NDArray[np.bool_] | None:
    """Return a foreground mask, or ``None`` when no background is separable.

    The mask keeps pixels whose colour differs from the border's dominant
    colour by more than the border's own noise.
    """
    ratio = separability_ratio(image)
    if ratio <= threshold:
        return None

    rgb = _rgb_array(image)
    border = _border_pixels(rgb)
    background = border.mean(axis=0)
    tolerance = max(float(border.std(axis=0).mean()) * 1.5, 0.05)
    distance = np.linalg.norm(rgb - background, axis=2)
    mask = distance > tolerance
    if mask.mean() < 0.05:
        return None
    return mask


def descriptor_mode(
    image: Image.Image,
    threshold: float = DEFAULT_THRESHOLD,
) -> str:
    """Return ``"segmented"`` or ``"variance"`` for the given image."""
    return "segmented" if separability_ratio(image) > threshold else "variance"
