"""Search helpers and persisted relevance-feedback sessions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from backend.database import get_db
from backend.fre import weighted_squared_euclidean
from backend.index import DatasetIndex


@dataclass
class SearchSession:
    owner_user_id: int
    index_fingerprint: str
    query_vector: NDArray[np.float32]
    weights: NDArray[np.float32]
    result_ids: list[int]
    excluded_id: int | None = None
    iteration: int = 0


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


def create_search_session(session_id: str, search_session: SearchSession) -> None:
    get_db().execute(
        """
        INSERT INTO search_sessions (
            id, user_id, index_fingerprint, query_vector, weights, result_ids,
            excluded_id, iteration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        _session_values(search_session, include_id=session_id),
    )
    get_db().commit()


def get_search_session(session_id: str, user_id: int) -> SearchSession | None:
    row = get_db().execute(
        """
        SELECT user_id, index_fingerprint, query_vector, weights, result_ids,
            excluded_id, iteration
        FROM search_sessions
        WHERE id = ? AND user_id = ?
        """,
        (session_id, user_id),
    ).fetchone()
    if row is None:
        return None

    try:
        query_vector = np.asarray(json.loads(row["query_vector"]), dtype=np.float32)
        weights = np.asarray(json.loads(row["weights"]), dtype=np.float32)
        result_ids = json.loads(row["result_ids"])
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise RuntimeError("La session de recherche stockée est illisible.") from error
    if (
        query_vector.ndim != 1
        or query_vector.size == 0
        or weights.shape != query_vector.shape
        or not np.isfinite(query_vector).all()
        or not np.isfinite(weights).all()
        or not isinstance(result_ids, list)
        or any(type(image_id) is not int for image_id in result_ids)
    ):
        raise RuntimeError("La session de recherche stockée contient des valeurs invalides.")

    excluded_id = row["excluded_id"]
    return SearchSession(
        owner_user_id=int(row["user_id"]),
        index_fingerprint=str(row["index_fingerprint"]),
        query_vector=query_vector,
        weights=weights,
        result_ids=result_ids,
        excluded_id=int(excluded_id) if excluded_id is not None else None,
        iteration=int(row["iteration"]),
    )


def update_search_session(session_id: str, search_session: SearchSession) -> None:
    cursor = get_db().execute(
        """
        UPDATE search_sessions
        SET query_vector = ?, weights = ?, result_ids = ?, excluded_id = ?,
            iteration = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
        WHERE id = ? AND user_id = ? AND index_fingerprint = ?
        """,
        _session_values(search_session)[2:]
        + (
            session_id,
            search_session.owner_user_id,
            search_session.index_fingerprint,
        ),
    )
    if cursor.rowcount != 1:
        raise RuntimeError("La session de recherche n'a pas pu être mise à jour.")
    get_db().commit()


def _session_values(
    search_session: SearchSession,
    include_id: str | None = None,
) -> tuple[object, ...]:
    values: tuple[object, ...] = (
        search_session.owner_user_id,
        search_session.index_fingerprint,
        json.dumps(search_session.query_vector.tolist(), allow_nan=False),
        json.dumps(search_session.weights.tolist(), allow_nan=False),
        json.dumps(search_session.result_ids),
        search_session.excluded_id,
        search_session.iteration,
    )
    if include_id is None:
        return values
    return (include_id, *values)


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
