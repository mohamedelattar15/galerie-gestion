"""Spatial weighting of descriptor pixels by local block variance.

A uniform region (typically the background) carries little information; a
textured region carries the subject. Weighting pixels by their block variance
rebalances the global histograms without discarding any information.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

DEFAULT_GRID = 4
MIN_BLOCK_WEIGHT = 0.05


def _check_rgb(rgb: NDArray[np.floating]) -> NDArray[np.float32]:
    values = np.asarray(rgb, dtype=np.float32)
    if values.ndim != 3 or values.shape[2] != 3:
        raise ValueError("L'image doit être un tableau RGB de forme (h, w, 3).")
    return values


def block_bounds(length: int, grid: int) -> list[tuple[int, int]]:
    """Split an axis of the given length into ``grid`` contiguous ranges."""
    if grid < 1:
        raise ValueError("grid doit être supérieur ou égal à 1.")
    edges = np.linspace(0, length, grid + 1).round().astype(int)
    return [(int(edges[i]), int(edges[i + 1])) for i in range(grid)]


def block_variances(rgb: NDArray[np.floating], grid: int = DEFAULT_GRID) -> NDArray[np.float32]:
    """Return the mean per-channel variance of every block, shape (grid, grid)."""
    values = _check_rgb(rgb)
    rows = block_bounds(values.shape[0], grid)
    columns = block_bounds(values.shape[1], grid)
    variances = np.zeros((grid, grid), dtype=np.float32)
    for row_index, (top, bottom) in enumerate(rows):
        for column_index, (left, right) in enumerate(columns):
            block = values[top:bottom, left:right]
            if block.size == 0:
                continue
            variances[row_index, column_index] = float(block.reshape(-1, 3).var(axis=0).mean())
    return variances


def block_weights(
    rgb: NDArray[np.floating],
    grid: int = DEFAULT_GRID,
    floor: float = MIN_BLOCK_WEIGHT,
) -> NDArray[np.float32]:
    """Return normalized block weights, shape (grid, grid), summing to one."""
    if not 0 <= floor < 1:
        raise ValueError("floor doit être compris entre 0 et 1.")
    variances = block_variances(rgb, grid)
    peak = float(variances.max())
    if peak <= 0:
        return np.full((grid, grid), 1.0 / variances.size, dtype=np.float32)
    normalized = variances / peak
    weights = floor + (1.0 - floor) * normalized
    return (weights / weights.sum()).astype(np.float32)


def pixel_weights(
    rgb: NDArray[np.floating],
    grid: int = DEFAULT_GRID,
    floor: float = MIN_BLOCK_WEIGHT,
) -> NDArray[np.float32]:
    """Expand block weights to a per-pixel weight map, shape (h, w)."""
    values = _check_rgb(rgb)
    weights = block_weights(values, grid, floor)
    rows = block_bounds(values.shape[0], grid)
    columns = block_bounds(values.shape[1], grid)
    result = np.zeros(values.shape[:2], dtype=np.float32)
    for row_index, (top, bottom) in enumerate(rows):
        for column_index, (left, right) in enumerate(columns):
            result[top:bottom, left:right] = weights[row_index, column_index]
    return result
