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

def test_extract_features_modes_keep_the_vector_shape() -> None:
    image = Image.new("RGB", (24, 24), (40, 160, 70))

    for mode in ("global", "variance", "adaptive"):
        descriptor = extract_features(image, mode=mode)
        assert descriptor.vector.shape == (FEATURE_DIMENSION,)
        assert (descriptor.vector == descriptor.vector).all()


def test_global_mode_is_the_default_and_unchanged() -> None:
    image = Image.new("RGB", (20, 20), (200, 30, 80))

    assert extract_features(image).vector.tolist() == extract_features(
        image, mode="global"
    ).vector.tolist()


def test_extract_features_rejects_an_unknown_mode() -> None:
    with pytest.raises(ValueError, match="mode"):
        extract_features(Image.new("RGB", (8, 8)), mode="unknown")


def test_variance_mode_downweights_a_uniform_background() -> None:
    image = Image.new("RGB", (32, 32), (20, 160, 40))
    image.paste(Image.new("RGB", (8, 8), (240, 60, 90)), (12, 12))

    global_descriptor = extract_features(image, mode="global")
    variance_descriptor = extract_features(image, mode="variance")

    assert variance_descriptor.vector.shape == global_descriptor.vector.shape
    assert variance_descriptor.vector.tolist() != global_descriptor.vector.tolist()
