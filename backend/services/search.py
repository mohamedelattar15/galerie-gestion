"""Application workflows for CBIR search and relevance feedback."""

from __future__ import annotations

from uuid import uuid4

import numpy as np
from numpy.typing import NDArray

from backend.database.repositories.search_sessions import (
    create_search_session,
    get_search_session,
    update_search_session,
)
from backend.domain.fre import compute_fre_weights
from backend.domain.models import DatasetIndex, SearchSession
from backend.domain.retrieval import rank_index


class SearchServiceError(ValueError):
    """A search workflow error with an HTTP-appropriate status code."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def start_search(
    index: DatasetIndex,
    query_vector: NDArray[np.floating],
    top_k: int,
    user_id: int,
    index_fingerprint: str,
    excluded_id: int | None = None,
) -> tuple[str, list[int], NDArray[np.float32]]:
    weights = np.ones(query_vector.size, dtype=np.float32)
    result_ids, distances = rank_index(
        index, query_vector, weights, top_k, excluded_id=excluded_id
    )
    session_id = uuid4().hex
    create_search_session(
        session_id,
        SearchSession(
            owner_user_id=user_id,
            index_fingerprint=index_fingerprint,
            query_vector=query_vector.copy(),
            weights=weights,
            result_ids=result_ids,
            excluded_id=excluded_id,
        ),
    )
    return session_id, result_ids, distances


def load_feedback_session(
    session_id: str,
    user_id: int,
    index_fingerprint: str,
) -> SearchSession:
    session = get_search_session(session_id, user_id)
    if session is None:
        raise SearchServiceError(
            "La session de recherche n'existe pas ou ne vous appartient pas.", 404
        )
    if session.index_fingerprint != index_fingerprint:
        raise SearchServiceError(
            "L'index de recherche a changé depuis cette session. Lancez une nouvelle recherche.",
            409,
        )
    return session


def apply_feedback(
    index: DatasetIndex,
    session_id: str,
    session: SearchSession,
    relevant_ids: list[int],
    non_relevant_ids: list[int],
    top_k: int,
) -> tuple[SearchSession, NDArray[np.float32]]:
    if not set(relevant_ids + non_relevant_ids).issubset(session.result_ids):
        raise SearchServiceError(
            "Le feedback doit porter sur les résultats de l'itération courante.", 422
        )
    if len(relevant_ids) < 2:
        raise SearchServiceError(
            "Sélectionnez au moins deux images pertinentes pour appliquer FRE.", 422
        )

    relevant_vectors = index.vectors[np.asarray(relevant_ids, dtype=np.int64)]
    try:
        weights = compute_fre_weights(relevant_vectors)
    except ValueError as error:
        raise SearchServiceError(str(error), 422) from error
    query_vector = relevant_vectors.mean(axis=0).astype(np.float32)
    result_ids, distances = rank_index(
        index,
        query_vector,
        weights,
        top_k,
        excluded_id=session.excluded_id,
    )

    session.query_vector = query_vector
    session.weights = weights
    session.result_ids = result_ids
    session.iteration += 1
    update_search_session(session_id, session)
    return session, distances
