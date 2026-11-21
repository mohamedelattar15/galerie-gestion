import numpy as np
from PIL import Image

from backend.domain.segmentation import (
    block_variance_weights,
    descriptor_mode,
    object_mask,
    separability_ratio,
)


def _object_on_background(size: int = 64) -> Image.Image:
    """Green background with a red square in the middle."""
    array = np.zeros((size, size, 3), dtype=np.uint8)
    array[:, :] = (20, 160, 40)
    start, stop = size // 4, size - size // 4
    array[start:stop, start:stop] = (220, 30, 30)
    return Image.fromarray(array)


def _uniform_image(size: int = 64, color: tuple[int, int, int] = (120, 120, 120)) -> Image.Image:
    return Image.new("RGB", (size, size), color)


def _textured_image(size: int = 64) -> Image.Image:
    rng = np.random.default_rng(0)
    return Image.fromarray(rng.integers(0, 256, (size, size, 3), dtype=np.uint8))


def test_separability_ratio_is_high_for_an_object_on_a_flat_background() -> None:
    assert separability_ratio(_object_on_background()) > 1.2


def test_separability_ratio_is_low_for_a_uniform_image() -> None:
    assert separability_ratio(_uniform_image()) < 1.2


def test_separability_ratio_is_low_for_a_texture() -> None:
    assert separability_ratio(_textured_image()) < 1.2


def test_block_weights_sum_to_one_and_favour_structured_blocks() -> None:
    weights = block_variance_weights(_object_on_background(), grid=4)

    assert weights.shape == (4, 4)
    assert float(weights.sum()) == np.float32(1.0) or abs(float(weights.sum()) - 1.0) < 1e-5
    center = weights[1:3, 1:3].mean()
    corners = np.mean([weights[0, 0], weights[0, 3], weights[3, 0], weights[3, 3]])
    assert center > corners


def test_block_weights_stay_uniform_on_a_flat_image() -> None:
    weights = block_variance_weights(_uniform_image(), grid=4)

    assert np.allclose(weights, 1.0 / 16, atol=1e-6)


def test_object_mask_isolates_the_foreground() -> None:
    mask = object_mask(_object_on_background())

    assert mask is not None
    assert mask.shape == (64, 64)
    assert mask[32, 32]
    assert not mask[2, 2]


def test_object_mask_is_none_without_a_separable_background() -> None:
    assert object_mask(_uniform_image()) is None
    assert object_mask(_textured_image()) is None


def test_descriptor_mode_selects_the_expected_strategy() -> None:
    assert descriptor_mode(_object_on_background()) == "segmented"
    assert descriptor_mode(_textured_image()) == "variance"
