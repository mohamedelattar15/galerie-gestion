import numpy as np
import pytest

from backend.domain.segmentation import (
    block_variances,
    block_weights,
    border_std,
    has_distinct_background,
    pixel_weights,
    safe_object_mask,
    separability_ratio,
)


def _object_on_background(background: tuple[int, int, int], subject: tuple[int, int, int]) -> np.ndarray:
    image = np.zeros((64, 64, 3), dtype=np.float32)
    image[:, :] = np.asarray(background, dtype=np.float32) / 255.0
    image[20:44, 20:44] = np.asarray(subject, dtype=np.float32) / 255.0
    return image


def _noise_image(seed: int = 0, size: int = 64) -> np.ndarray:
    return np.random.default_rng(seed).random((size, size, 3), dtype=np.float32)


def test_uniform_background_with_contrasted_subject_is_separable() -> None:
    image = _object_on_background((20, 160, 40), (240, 60, 90))

    assert border_std(image) < 0.01
    assert separability_ratio(image) > 1.2
    assert has_distinct_background(image, threshold=1.2)


def test_uniform_noise_has_no_distinct_background() -> None:
    image = _noise_image()

    assert separability_ratio(image) < 1.2
    assert not has_distinct_background(image, threshold=1.2)


def test_separability_rejects_invalid_shapes() -> None:
    with pytest.raises(ValueError, match="RGB"):
        separability_ratio(np.zeros((10, 10), dtype=np.float32))


def test_block_variances_peak_on_the_textured_block() -> None:
    image = np.zeros((64, 64, 3), dtype=np.float32)
    image[:32, :32] = _noise_image(size=32)

    variances = block_variances(image, grid=2)

    assert variances[0, 0] == pytest.approx(variances.max())
    assert variances[1, 1] == pytest.approx(0.0)


def test_block_weights_are_normalized_and_favour_texture() -> None:
    image = np.zeros((64, 64, 3), dtype=np.float32)
    image[:32, :32] = _noise_image(size=32)

    weights = block_weights(image, grid=2)

    assert weights.sum() == pytest.approx(1.0, abs=1e-6)
    assert weights[0, 0] > weights[1, 1]


def test_pixel_weights_match_the_image_shape() -> None:
    image = _noise_image()

    weights = pixel_weights(image, grid=4)

    assert weights.shape == image.shape[:2]
    assert np.isfinite(weights).all()
    assert (weights > 0).all()


def test_object_mask_keeps_the_subject_on_a_uniform_background() -> None:
    image = _object_on_background((20, 160, 40), (240, 60, 90))

    mask = safe_object_mask(image, tolerance=0.18)

    assert mask is not None
    assert mask[32, 32]
    assert not mask[0, 0]


def test_safe_object_mask_rejects_a_failed_segmentation() -> None:
    image = _noise_image()

    assert safe_object_mask(image) is None
