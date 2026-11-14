"""Data models shared by CBIR algorithms and application services."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from backend.domain.normalization import FeatureNormalizer


@dataclass(frozen=True)
class DatasetIndex:
    paths: tuple[str, ...]
    labels: tuple[str, ...]
    vectors: NDArray[np.float32]
    normalizer: FeatureNormalizer


@dataclass
class SearchSession:
    owner_user_id: int
    index_fingerprint: str
    query_vector: NDArray[np.float32]
    weights: NDArray[np.float32]
    result_ids: list[int]
    excluded_id: int | None = None
    iteration: int = 0
