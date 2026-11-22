"""Consistent corpus-fitted normalization for descriptor vectors."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from backend.domain.features import (
    COLOR_HISTOGRAM_SLICE,
    FEATURE_DIMENSION,
    LBP_SLICE,
    STANDARDIZED_SLICE,
)

FloatArray = NDArray[np.float32]
FEATURE_TRANSFORM_VERSION = "hellinger-v1"
HISTOGRAM_SLICES = (COLOR_HISTOGRAM_SLICE, LBP_SLICE)


@dataclass(frozen=True)
class FeatureNormalizer:
    mean: FloatArray
    scale: FloatArray

    @classmethod
    def fit(cls, vectors: NDArray[np.floating]) -> "FeatureNormalizer":
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] == 0:
            raise ValueError("L'index doit contenir au moins un vecteur 2D.")
        if matrix.shape[1] != FEATURE_DIMENSION:
            raise ValueError(f"Chaque vecteur doit avoir {FEATURE_DIMENSION} dimensions.")
        if not np.isfinite(matrix).all():
            raise ValueError("Les vecteurs doivent contenir uniquement des valeurs finies.")

        scalar_features = matrix[:, STANDARDIZED_SLICE]
        mean = scalar_features.mean(axis=0)
        scale = scalar_features.std(axis=0)
        scale[scale < 1e-12] = 1.0
        return cls(mean=mean.astype(np.float32), scale=scale.astype(np.float32))

    def transform(self, vectors: NDArray[np.floating]) -> FloatArray:
        values = np.asarray(vectors, dtype=np.float32)
        if values.ndim not in (1, 2) or values.shape[-1] != FEATURE_DIMENSION:
            raise ValueError(f"Chaque vecteur doit avoir {FEATURE_DIMENSION} dimensions.")
        if not np.isfinite(values).all():
            raise ValueError("Les vecteurs doivent contenir uniquement des valeurs finies.")

        result = values.copy()
        for histogram_slice in HISTOGRAM_SLICES:
            histogram = result[..., histogram_slice]
            if np.any(histogram < 0):
                raise ValueError("Les histogrammes doivent contenir des valeurs positives ou nulles.")
            result[..., histogram_slice] = np.sqrt(histogram)
        result[..., STANDARDIZED_SLICE] = (
            result[..., STANDARDIZED_SLICE] - self.mean
        ) / self.scale
        return result
