import numpy as np
import pytest
from PIL import Image

from backend.domain.features import (
    COLOR_HISTOGRAM_SLICE,
    FEATURE_DIMENSION,
    LBP_SLICE,
    extract_features,
)
from backend.domain.normalization import FeatureNormalizer


def test_extract_features_returns_fixed_size_normalized_histograms() -> None:
    descriptor = extract_features(Image.new("RGB", (18, 12), (200, 30, 80)))
    vector = descriptor.vector

    assert vector.shape == (FEATURE_DIMENSION,)
    assert vector.dtype.name == "float32"
    assert (vector == vector).all()
    assert abs(float(vector[COLOR_HISTOGRAM_SLICE][:16].sum()) - 1.0) < 1e-6
    assert abs(float(vector[COLOR_HISTOGRAM_SLICE][16:32].sum()) - 1.0) < 1e-6
    assert abs(float(vector[COLOR_HISTOGRAM_SLICE][32:48].sum()) - 1.0) < 1e-6
    assert abs(float(vector[LBP_SLICE].sum()) - 1.0) < 1e-6


def test_extract_features_handles_tiny_images() -> None:
    descriptor = extract_features(Image.new("RGB", (1, 1), (255, 255, 255)))

    assert descriptor.vector.shape == (FEATURE_DIMENSION,)
    assert (descriptor.vector == descriptor.vector).all()
    assert descriptor.dominant_colors[-3:].tolist() == [1.0, 0.0, 0.0]


def test_extract_features_accepts_every_descriptor_mode() -> None:
    image = Image.new("RGB", (32, 32), (200, 30, 80))

    for mode in ("global", "variance", "segmented", "adaptive"):
        descriptor = extract_features(image, mode=mode)
        assert descriptor.vector.shape == (FEATURE_DIMENSION,)
        assert np.isfinite(descriptor.vector).all()


def test_extract_features_rejects_an_unknown_mode() -> None:
    with pytest.raises(ValueError, match="mode"):
        extract_features(Image.new("RGB", (8, 8), (0, 0, 0)), mode="unknown")


def test_segmented_mode_ignores_a_uniform_background() -> None:
    array = np.zeros((64, 64, 3), dtype=np.uint8)
    array[:, :] = (20, 160, 40)
    array[16:48, 16:48] = (220, 30, 30)
    image = Image.fromarray(array)

    global_descriptor = extract_features(image, mode="global")
    segmented_descriptor = extract_features(image, mode="segmented")

    # The red object dominates the segmented hue histogram, not the green background.
    red_bin = global_descriptor.color_histogram[0:16].argmax()
    segmented_red_bin = segmented_descriptor.color_histogram[0:16].argmax()
    assert red_bin != segmented_red_bin
    assert segmented_descriptor.color_moments[0] > 0.5


def test_variance_mode_changes_the_descriptors_of_a_structured_image() -> None:
    array = np.zeros((64, 64, 3), dtype=np.uint8)
    array[:, :] = (20, 160, 40)
    array[16:48, 16:48] = (220, 30, 30)
    image = Image.fromarray(array)

    global_vector = extract_features(image, mode="global").vector
    variance_vector = extract_features(image, mode="variance").vector

    assert not np.allclose(global_vector, variance_vector)
    assert variance_vector.shape == (FEATURE_DIMENSION,)


def test_variance_mode_matches_global_mode_on_a_flat_image() -> None:
    image = Image.new("RGB", (32, 32), (120, 120, 120))

    global_vector = extract_features(image, mode="global").vector
    variance_vector = extract_features(image, mode="variance").vector

    # A flat image has no structure: only float rounding may differ.
    assert np.allclose(global_vector, variance_vector, atol=1e-4)


def test_normalizer_reuses_corpus_parameters_and_preserves_histograms() -> None:
    vectors = [
        extract_features(Image.new("RGB", (12, 12), color)).vector
        for color in ((255, 0, 0), (0, 255, 0), (0, 0, 255))
    ]
    normalizer = FeatureNormalizer.fit(vectors)
    transformed = normalizer.transform(vectors)

    assert transformed.shape == (3, FEATURE_DIMENSION)
    assert abs(float(transformed[0, COLOR_HISTOGRAM_SLICE][:16].sum()) - 1.0) < 1e-6
    assert (transformed == transformed).all()
