"""Fixed-size color and texture descriptors for CBIR images."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from backend.domain.segmentation.blocks import pixel_weights
from backend.domain.segmentation.mask import DEFAULT_TOLERANCE as DEFAULT_MASK_TOLERANCE
from backend.domain.segmentation.mask import safe_object_mask
from backend.domain.segmentation.separability import has_distinct_background

COLOR_HISTOGRAM_BINS = 16
DOMINANT_COLOR_COUNT = 3
GLCM_LEVELS = 16
LBP_BINS = 256
MAX_IMAGE_SIDE = 256
DESCRIPTOR_MODES = ("global", "variance", "adaptive")

COLOR_HISTOGRAM_SLICE = slice(0, 3 * COLOR_HISTOGRAM_BINS)
COLOR_MOMENTS_SLICE = slice(COLOR_HISTOGRAM_SLICE.stop, COLOR_HISTOGRAM_SLICE.stop + 9)
DOMINANT_COLORS_SLICE = slice(COLOR_MOMENTS_SLICE.stop, COLOR_MOMENTS_SLICE.stop + 12)
GLCM_SLICE = slice(DOMINANT_COLORS_SLICE.stop, DOMINANT_COLORS_SLICE.stop + 4)
LBP_SLICE = slice(GLCM_SLICE.stop, GLCM_SLICE.stop + LBP_BINS)
FEATURE_DIMENSION = LBP_SLICE.stop
STANDARDIZED_SLICE = slice(COLOR_HISTOGRAM_SLICE.stop, LBP_SLICE.start)


@dataclass(frozen=True)
class ImageDescriptor:
    """Named descriptor blocks with a stable concatenation order."""

    color_histogram: np.ndarray
    color_moments: np.ndarray
    dominant_colors: np.ndarray
    glcm: np.ndarray
    lbp_histogram: np.ndarray

    @property
    def vector(self) -> np.ndarray:
        return np.concatenate(
            (
                self.color_histogram,
                self.color_moments,
                self.dominant_colors,
                self.glcm,
                self.lbp_histogram,
            )
        ).astype(np.float32, copy=False)

    def to_dict(self) -> dict[str, list[float]]:
        return {
            "color_histogram": self.color_histogram.tolist(),
            "color_moments": self.color_moments.tolist(),
            "dominant_colors": self.dominant_colors.tolist(),
            "glcm": self.glcm.tolist(),
            "lbp_histogram": self.lbp_histogram.tolist(),
        }


def _prepare_image(image: Image.Image) -> Image.Image:
    if image.width < 1 or image.height < 1:
        raise ValueError("L'image doit avoir une largeur et une hauteur positives.")

    rgb_image = image.convert("RGB")
    largest_side = max(rgb_image.size)
    if largest_side > MAX_IMAGE_SIDE:
        scale = MAX_IMAGE_SIDE / largest_side
        size = (max(1, round(rgb_image.width * scale)), max(1, round(rgb_image.height * scale)))
        rgb_image = rgb_image.resize(size, Image.Resampling.BILINEAR)

    if min(rgb_image.size) < 3:
        size = (max(3, rgb_image.width), max(3, rgb_image.height))
        rgb_image = rgb_image.resize(size, Image.Resampling.BILINEAR)
    return rgb_image


def _color_histogram(
    rgb_image: Image.Image,
    weights: np.ndarray | None = None,
) -> np.ndarray:
    hsv = np.asarray(rgb_image.convert("HSV"), dtype=np.uint8)
    if weights is None:
        weights = np.ones(hsv.shape[:2], dtype=np.float32)
    else:
        weights = np.asarray(weights, dtype=np.float32)
        if weights.shape != hsv.shape[:2]:
            raise ValueError("La carte de poids doit avoir la taille de l'image.")
    total_weight = float(weights.sum())
    if total_weight <= 0:
        raise ValueError("La carte de poids est vide.")

    bins: list[np.ndarray] = []
    for channel in range(3):
        indices = (hsv[:, :, channel] // (256 // COLOR_HISTOGRAM_BINS)).ravel()
        counts = np.bincount(
            indices,
            weights=weights.ravel(),
            minlength=COLOR_HISTOGRAM_BINS,
        )
        bins.append(counts.astype(np.float32) / total_weight)
    return np.concatenate(bins)


def _color_moments(
    rgb_image: Image.Image,
    weights: np.ndarray | None = None,
) -> np.ndarray:
    values = np.asarray(rgb_image, dtype=np.float32) / 255.0
    if weights is None:
        means = values.mean(axis=(0, 1))
        centered = values - means
        standard_deviations = np.sqrt(np.mean(centered**2, axis=(0, 1)))
        third_moments = np.mean(centered**3, axis=(0, 1))
    else:
        weight_map = np.asarray(weights, dtype=np.float32)
        if weight_map.shape != values.shape[:2]:
            raise ValueError("La carte de poids doit avoir la taille de l'image.")
        total_weight = float(weight_map.sum())
        if total_weight <= 0:
            raise ValueError("La carte de poids est vide.")
        means = (values * weight_map[:, :, None]).sum(axis=(0, 1)) / total_weight
        centered = values - means
        standard_deviations = np.sqrt(
            ((centered**2) * weight_map[:, :, None]).sum(axis=(0, 1)) / total_weight
        )
        third_moments = (
            (centered**3) * weight_map[:, :, None]
        ).sum(axis=(0, 1)) / total_weight
    skewness = np.divide(
        third_moments,
        standard_deviations**3,
        out=np.zeros_like(third_moments),
        where=standard_deviations > 1e-12,
    )
    return np.concatenate((means, standard_deviations, skewness)).astype(np.float32)


def _dominant_colors(rgb_image: Image.Image) -> np.ndarray:
    quantized = rgb_image.quantize(
        colors=DOMINANT_COLOR_COUNT,
        method=Image.Quantize.MEDIANCUT,
    )
    palette = quantized.getpalette()
    if palette is None:
        raise ValueError("Impossible de calculer les couleurs dominantes de l'image.")

    labels = np.asarray(quantized, dtype=np.uint8)
    counts = np.bincount(labels.ravel(), minlength=256)
    active_labels = np.flatnonzero(counts)
    ordered_labels = sorted(active_labels, key=lambda label: (-counts[label], label))
    selected: list[int | None] = ordered_labels[:DOMINANT_COLOR_COUNT]
    while len(selected) < DOMINANT_COLOR_COUNT:
        selected.append(None)

    total = int(counts.sum())
    values: list[float] = []
    proportions: list[float] = []
    for label in selected:
        palette_label = selected[0] if label is None else label
        if palette_label is None:
            raise RuntimeError("Aucune couleur dominante n'a été détectée.")
        start = palette_label * 3
        values.extend(float(component) / 255.0 for component in palette[start : start + 3])
        proportions.append(float(counts[label]) / total if label is not None else 0.0)
    return np.asarray(values + proportions, dtype=np.float32)


def _glcm_properties(rgb_image: Image.Image) -> np.ndarray:
    gray = np.asarray(rgb_image.convert("L"), dtype=np.uint8) // (256 // GLCM_LEVELS)
    offsets = (
        (gray[:, :-1], gray[:, 1:]),
        (gray[:-1, :-1], gray[1:, 1:]),
        (gray[:-1, :], gray[1:, :]),
        (gray[:-1, 1:], gray[1:, :-1]),
    )
    levels = np.arange(GLCM_LEVELS, dtype=np.float64)
    properties: list[np.ndarray] = []

    for source, target in offsets:
        encoded = source.ravel() * GLCM_LEVELS + target.ravel()
        matrix = np.bincount(encoded, minlength=GLCM_LEVELS**2).reshape(
            GLCM_LEVELS, GLCM_LEVELS
        )
        matrix = matrix.astype(np.float64)
        matrix += matrix.T
        total = matrix.sum()
        if total == 0:
            raise ValueError("L'image est trop petite pour calculer la texture GLCM.")
        matrix /= total

        row_mean = float((matrix * levels[:, None]).sum())
        column_mean = float((matrix * levels[None, :]).sum())
        row_std = float(np.sqrt((matrix * (levels[:, None] - row_mean) ** 2).sum()))
        column_std = float(
            np.sqrt((matrix * (levels[None, :] - column_mean) ** 2).sum())
        )
        difference = levels[:, None] - levels[None, :]
        contrast = float((matrix * difference**2).sum())
        if row_std * column_std == 0:
            correlation = 1.0
        else:
            correlation = float(
                (
                    matrix
                    * (levels[:, None] - row_mean)
                    * (levels[None, :] - column_mean)
                ).sum()
                / (row_std * column_std)
            )
        energy = float((matrix**2).sum())
        homogeneity = float((matrix / (1.0 + difference**2)).sum())
        properties.append(
            np.asarray((contrast, correlation, energy, homogeneity), dtype=np.float64)
        )

    return np.mean(properties, axis=0).astype(np.float32)


def _lbp_histogram(
    rgb_image: Image.Image,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    gray = np.asarray(rgb_image.convert("L"), dtype=np.uint8)
    center = gray[1:-1, 1:-1]
    code = np.zeros(center.shape, dtype=np.uint8)
    neighbors = (
        gray[:-2, :-2],
        gray[:-2, 1:-1],
        gray[:-2, 2:],
        gray[1:-1, 2:],
        gray[2:, 2:],
        gray[2:, 1:-1],
        gray[2:, :-2],
        gray[1:-1, :-2],
    )
    for bit, neighbor in enumerate(neighbors):
        code |= (neighbor >= center).astype(np.uint8) << bit

    if mask is None:
        counts = np.bincount(code.ravel(), minlength=LBP_BINS).astype(np.float32)
        return counts / counts.sum()

    inner_mask = np.asarray(mask, dtype=bool)[1:-1, 1:-1]
    selected = code[inner_mask]
    if selected.size == 0:
        counts = np.bincount(code.ravel(), minlength=LBP_BINS).astype(np.float32)
        return counts / counts.sum()
    counts = np.bincount(selected, minlength=LBP_BINS).astype(np.float32)
    return counts / counts.sum()


def extract_features(
    image: Image.Image,
    mode: str = "global",
    separability_threshold: float = 1.2,
    block_grid: int = 4,
) -> ImageDescriptor:
    """Extract normalized histograms and raw numeric descriptors from an image.

    ``mode`` selects how the background is handled:

    - ``"global"``: the whole image is used, exactly as before;
    - ``"variance"``: pixels are weighted by their block variance, so a uniform
      background contributes less without being discarded;
    - ``"adaptive"``: segmentation is applied only when the image has a
      distinct background, otherwise the variance weighting is used.
    """
    if mode not in DESCRIPTOR_MODES:
        raise ValueError(f"mode doit être l'un de {DESCRIPTOR_MODES}.")
    rgb_image = _prepare_image(image)
    weights: np.ndarray | None = None
    mask: np.ndarray | None = None

    if mode in {"variance", "adaptive"}:
        weights = pixel_weights(
            np.asarray(rgb_image, dtype=np.float32) / 255.0,
            grid=block_grid,
        )
    if mode == "adaptive":
        candidate = safe_object_mask(
            np.asarray(rgb_image, dtype=np.float32) / 255.0,
            tolerance=DEFAULT_MASK_TOLERANCE,
        )
        if candidate is not None and has_distinct_background(
            np.asarray(rgb_image, dtype=np.float32) / 255.0,
            threshold=separability_threshold,
        ):
            mask = candidate
            weights = None

    descriptor = ImageDescriptor(
        color_histogram=_color_histogram(rgb_image, weights),
        color_moments=_color_moments(rgb_image, weights),
        dominant_colors=_dominant_colors(rgb_image),
        glcm=_glcm_properties(rgb_image),
        lbp_histogram=_lbp_histogram(rgb_image, mask),
    )
    if descriptor.vector.shape != (FEATURE_DIMENSION,):
        raise RuntimeError("L'extracteur a produit un vecteur de dimension inattendue.")
    if not np.isfinite(descriptor.vector).all():
        raise RuntimeError("L'extracteur a produit des valeurs non finies.")
    return descriptor
