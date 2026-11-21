"""Background separability measurement.

The descriptors of an image are dominated by its background when the
background is uniform and occupies most of the surface. This module measures
that property so the feature extractor can decide, image by image, whether
segmentation is worth applying.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

BORDER_MARGIN = 0.15
CENTER_INSET = 0.25
MIN_STD = 1e-6


def _check_rgb(rgb: NDArray[np.floating]) -> NDArray[np.float32]:
    values = np.asarray(rgb, dtype=np.float32)
    if values.ndim != 3 or values.shape[2] != 3:
        raise ValueError("L'image doit être un tableau RGB de forme (h, w, 3).")
    if values.shape[0] < 4 or values.shape[1] < 4:
        raise ValueError("L'image est trop petite pour mesurer la séparabilité.")
    return values


def border_pixels(rgb: NDArray[np.floating], margin: float = BORDER_MARGIN) -> NDArray[np.float32]:
    """Return the pixels of the outer frame as an (n, 3) matrix."""
    values = _check_rgb(rgb)
    height, width, _ = values.shape
    band = max(1, int(min(height, width) * margin))
    return np.concatenate(
        (
            values[:band].reshape(-1, 3),
            values[-band:].reshape(-1, 3),
            values[:, :band].reshape(-1, 3),
            values[:, -band:].reshape(-1, 3),
        )
    )


def center_pixels(rgb: NDArray[np.floating], inset: float = CENTER_INSET) -> NDArray[np.float32]:
    """Return the pixels of the central region as an (n, 3) matrix."""
    values = _check_rgb(rgb)
    height, width, _ = values.shape
    top = max(0, int(height * inset))
    bottom = max(top + 1, height - top)
    left = max(0, int(width * inset))
    right = max(left + 1, width - left)
    return values[top:bottom, left:right].reshape(-1, 3)


def border_std(rgb: NDArray[np.floating]) -> float:
    """Mean per-channel standard deviation of the border pixels."""
    return float(border_pixels(rgb).std(axis=0).mean())


def border_center_gap(rgb: NDArray[np.floating]) -> float:
    """Euclidean distance between the mean border colour and the mean centre colour."""
    border_mean = border_pixels(rgb).mean(axis=0)
    center_mean = center_pixels(rgb).mean(axis=0)
    return float(np.linalg.norm(border_mean - center_mean))


def separability_ratio(rgb: NDArray[np.floating]) -> float:
    """Ratio between the border/centre gap and the border dispersion.

    A high value means the centre differs from a homogeneous border, which is
    the signature of an object standing on a uniform background.
    """
    return border_center_gap(rgb) / max(border_std(rgb), MIN_STD)


def has_distinct_background(rgb: NDArray[np.floating], threshold: float) -> bool:
    """Tell whether the image has a background distinct enough to be segmented."""
    return separability_ratio(rgb) > threshold
