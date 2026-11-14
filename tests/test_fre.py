import numpy as np
import pytest

from backend.domain.fre import compute_fre_weights, weighted_squared_euclidean


def test_fre_weights_follow_inverse_relevant_standard_deviation() -> None:
    relevant = np.asarray([[0.0, 0.0], [0.0, 2.0]], dtype=np.float32)

    weights = compute_fre_weights(relevant)

    assert weights[0] == pytest.approx(1.0 / 0.0001)
    assert weights[1] == pytest.approx(1.0 / 1.0001)


def test_fre_rejects_fewer_than_two_relevant_examples() -> None:
    with pytest.raises(ValueError, match="au moins 2"):
        compute_fre_weights(np.asarray([[0.0, 1.0]], dtype=np.float32))


def test_weighted_squared_distance_matches_project_formula() -> None:
    distances = weighted_squared_euclidean(
        np.asarray([0.0, 0.0]),
        np.asarray([[1.0, 2.0], [0.0, 0.0]]),
        np.asarray([1.0, 3.0]),
    )

    assert distances.tolist() == pytest.approx([3.25, 0.0])


def test_weighted_distance_rejects_invalid_weights() -> None:
    with pytest.raises(ValueError, match="poids"):
        weighted_squared_euclidean(
            np.asarray([0.0]),
            np.asarray([[1.0]]),
            np.asarray([0.0]),
        )
