"""Feature Relevance Estimation and weighted retrieval distances."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float32]


def compute_fre_weights(
    relevant_vectors: NDArray[np.floating],
    epsilon: float = 0.0001,
    minimum_relevant: int = 2,
) -> FloatArray:
    """Calculate FRE weights from relevant examples in the current iteration."""
    vectors = np.asarray(relevant_vectors, dtype=np.float32)
    if vectors.ndim != 2:
        raise ValueError("Les vecteurs pertinents doivent former une matrice 2D.")
    if vectors.shape[0] < minimum_relevant:
        raise ValueError(
            f"FRE nécessite au moins {minimum_relevant} images pertinentes."
        )
    if vectors.shape[1] == 0:
        raise ValueError("Les vecteurs pertinents ne peuvent pas être vides.")
    if not np.isfinite(vectors).all():
        raise ValueError("Les vecteurs pertinents doivent contenir des valeurs finies.")
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("Epsilon doit être une valeur finie strictement positive.")

    standard_deviations = vectors.std(axis=0, ddof=0)
    weights = 1.0 / (epsilon + standard_deviations)
    return weights.astype(np.float32)


def weighted_squared_euclidean(
    query: NDArray[np.floating],
    candidates: NDArray[np.floating],
    weights: NDArray[np.floating],
) -> FloatArray:
    """Return normalized weighted squared-Euclidean distances for candidates."""
    query_vector = np.asarray(query, dtype=np.float32)
    candidate_matrix = np.asarray(candidates, dtype=np.float32)
    weight_vector = np.asarray(weights, dtype=np.float32)

    if query_vector.ndim != 1 or candidate_matrix.ndim != 2 or weight_vector.ndim != 1:
        raise ValueError("La requête, les candidats et les poids ont des dimensions invalides.")
    if candidate_matrix.shape[1] != query_vector.size or weight_vector.size != query_vector.size:
        raise ValueError("La requête, les candidats et les poids doivent avoir la même dimension.")
    if not (
        np.isfinite(query_vector).all()
        and np.isfinite(candidate_matrix).all()
        and np.isfinite(weight_vector).all()
    ):
        raise ValueError("Les vecteurs et les poids doivent contenir des valeurs finies.")
    if np.any(weight_vector < 0) or float(weight_vector.sum()) <= 0:
        raise ValueError("Les poids doivent être positifs et leur somme non nulle.")

    squared_differences = (candidate_matrix - query_vector) ** 2
    distances = squared_differences @ weight_vector / weight_vector.sum()
    return distances.astype(np.float32)
