"""Persistence operations for relevance-feedback search sessions."""

from __future__ import annotations

import json

import numpy as np

from backend.database.connection import get_db
from backend.domain.models import SearchSession


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
