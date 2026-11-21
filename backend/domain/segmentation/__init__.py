"""Background-aware helpers for descriptor computation.

The package exposes three independent building blocks:

- :mod:`separability` measures whether an image has a distinct background;
- :mod:`blocks` builds spatial weights from local block variance;
- :mod:`mask` derives an object mask from the dominant border colour.

They are pure NumPy functions with no dependency on Flask, SQLite or Pillow,
so they can be unit-tested in isolation.
"""

from backend.domain.segmentation.blocks import (
    block_bounds,
    block_variances,
    block_weights,
    pixel_weights,
)
from backend.domain.segmentation.mask import (
    background_color,
    color_distance_map,
    is_plausible,
    object_mask,
    safe_object_mask,
)
from backend.domain.segmentation.separability import (
    border_center_gap,
    border_pixels,
    border_std,
    center_pixels,
    has_distinct_background,
    separability_ratio,
)

__all__ = [
    "background_color",
    "block_bounds",
    "block_variances",
    "block_weights",
    "border_center_gap",
    "border_pixels",
    "border_std",
    "center_pixels",
    "color_distance_map",
    "has_distinct_background",
    "is_plausible",
    "object_mask",
    "pixel_weights",
    "safe_object_mask",
    "separability_ratio",
]
