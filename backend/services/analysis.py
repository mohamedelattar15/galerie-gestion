"""Background-separation analysis for gallery images."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from backend.domain.fre_config import DEFAULT_SEPARABILITY_THRESHOLD
from backend.domain.segmentation.mask import color_distance_map, is_plausible, object_mask
from backend.domain.segmentation.separability import separability_ratio

ANALYSIS_MAX_SIDE = 256


def _analysis_rgb(image: Image.Image) -> NDArray[np.float32]:
    rgb_image = image.convert("RGB")
    longest_side = max(rgb_image.size)
    if longest_side > ANALYSIS_MAX_SIDE:
        scale = ANALYSIS_MAX_SIDE / longest_side
        size = (
            max(4, round(rgb_image.width * scale)),
            max(4, round(rgb_image.height * scale)),
        )
        rgb_image = rgb_image.resize(size, Image.Resampling.BILINEAR)
    if min(rgb_image.size) < 4:
        raise ValueError("L'image doit mesurer au moins 4 × 4 pixels pour cette analyse.")
    return np.asarray(rgb_image, dtype=np.float32) / 255.0


def analyze_image(image: Image.Image) -> dict[str, float | str | bool]:
    """Measure background separation and recommend a descriptor mode."""
    rgb = _analysis_rgb(image)
    mask = object_mask(rgb)
    ratio = separability_ratio(rgb)
    mask_fraction = float(mask.mean())
    mask_available = is_plausible(mask)
    has_distinct_background = ratio > DEFAULT_SEPARABILITY_THRESHOLD
    recommended_mode = (
        "adaptive" if has_distinct_background and mask_available else "variance"
    )
    return {
        "separability_ratio": float(ratio),
        "recommended_mode": recommended_mode,
        "mask_fraction": mask_fraction,
        "mask_available": mask_available,
    }


def render_mask(image: Image.Image) -> Image.Image:
    """Render a binary object mask, white for object and black for background."""
    rgb = _analysis_rgb(image)
    mask = object_mask(rgb)
    if not is_plausible(mask):
        raise ValueError("Le masque n'est pas assez fiable pour être affiché.")
    values = np.where(mask, 255, 0).astype(np.uint8)
    return Image.fromarray(values, mode="L")


def render_background_map(image: Image.Image) -> Image.Image:
    """Render a grayscale distance map from the estimated border background."""
    rgb = _analysis_rgb(image)
    distances = color_distance_map(rgb)
    scale = float(np.percentile(distances, 95))
    if scale <= 1e-8:
        values = np.zeros(distances.shape, dtype=np.uint8)
    else:
        values = np.clip(distances / scale, 0.0, 1.0)
        values = np.round(values * 255).astype(np.uint8)
    return Image.fromarray(values, mode="L")
