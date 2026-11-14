"""Search helpers and in-memory relevance-feedback sessions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from backend.fre import weighted_squared_euclidean
from backend.index import DatasetIndex


@dataclass
class SearchSession:
    owner_user_id: int
    query_vector: NDArray[np.float32]
    weights: NDArray[np.float32]
    result_ids: list[int]
    excluded_id: int | None = None
    iteration: int = 0


def rank_index(
    index: DatasetIndex,
    query_vector: NDArray[np.floating],
    weights: NDArray[np.floating],
    top_k: int,
    excluded_id: int | None = None,
) -> tuple[list[int], NDArray[np.float32]]:
    if top_k < 1:
        raise ValueError("top_k doit être supérieur ou égal à 1.")
    distances = weighted_squared_euclidean(query_vector, index.vectors, weights)
    candidate_ids = np.arange(len(index.paths), dtype=np.int64)
    if excluded_id is not None:
        candidate_ids = candidate_ids[candidate_ids != excluded_id]
    order = np.argsort(distances[candidate_ids], kind="stable")[:top_k]
    result_ids = candidate_ids[order].tolist()
    return [int(value) for value in result_ids], distances
