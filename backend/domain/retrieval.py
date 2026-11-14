"""Pure helpers for CBIR ranking and index identity."""

from __future__ import annotations

import hashlib
import json

import numpy as np
from numpy.typing import NDArray

from backend.domain.fre import weighted_squared_euclidean
from backend.domain.models import DatasetIndex


def index_fingerprint(index: DatasetIndex) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            [index.paths, index.labels],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    for values in (index.vectors, index.normalizer.mean, index.normalizer.scale):
        array = np.ascontiguousarray(values, dtype=np.float32)
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


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
