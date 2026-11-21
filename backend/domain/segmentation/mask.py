"""Object mask derived from the dominant border colour.

The border of a photograph is almost always background. Pixels whose colour is
close to the mean border colour are treated as background and excluded from the
descriptor computation. The mask is only returned when it is plausible, so a
failed segmentation can never replace the global descriptors.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from backend.domain.segmentation.separability import border_pixels

DEFAULT_TOLERANCE = 0.18
MIN_OBJECT_FRACTION = 0.08
MAX_OBJECT_FRACTION = 0.95


def _check_rgb(rgb: NDArray[np.floating]) -> NDArray[np.float32]:
    values = np.asarray(rgb, dtype=np.float32)
    if values.ndim != 3 or values.shape[2] != 3:
        raise ValueError("L'image doit être un tableau RGB de forme (h, w, 3).")
    return values


def background_color(rgb: NDArray[np.floating]) -> NDArray[np.float32]:
    """Return the mean border colour, used as the background reference."""
    return border_pixels(rgb).mean(axis=0).astype(np.float32)


def color_distance_map(rgb: NDArray[np.floating]) -> NDArray[np.float32]:
    """Return the per-pixel distance to the background colour, shape (h, w)."""
    values = _check_rgb(rgb)
    reference = background_color(values)
    return np.linalg.norm(values - reference, axis=2).astype(np.float32)


def object_mask(rgb: NDArray[np.floating], tolerance: float = DEFAULT_TOLERANCE) -> NDArray[np.bool_]:
    """Return a boolean mask of the pixels that differ from the background."""
    if tolerance <= 0:
        raise ValueError("tolerance doit être strictement positive.")
    return color_distance_map(rgb) > tolerance


def is_plausible(mask: NDArray[np.bool_]) -> bool:
    """Tell whether a mask keeps a reasonable share of the image."""
    fraction = float(mask.mean()) if mask.size else 0.0
    return MIN_OBJECT_FRACTION <= fraction <= MAX_OBJECT_FRACTION


def safe_object_mask(
    rgb: NDArray[np.floating],
    tolerance: float = DEFAULT_TOLERANCE,
) -> NDArray[np.bool_] | None:
    """Return the object mask, or ``None`` when segmentation is not trustworthy."""
    candidate = object_mask(rgb, tolerance)
    return candidate if is_plausible(candidate) else None
