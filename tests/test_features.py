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


def test_normalizer_reuses_corpus_parameters_and_uses_hellinger_histograms() -> None:
    vectors = [
        extract_features(Image.new("RGB", (12, 12), color)).vector
        for color in ((255, 0, 0), (0, 255, 0), (0, 0, 255))
    ]
    normalizer = FeatureNormalizer.fit(vectors)
    transformed = normalizer.transform(vectors)

    assert transformed.shape == (3, FEATURE_DIMENSION)
    assert abs(float(np.square(transformed[0, COLOR_HISTOGRAM_SLICE][:16]).sum()) - 1.0) < 1e-6
    assert abs(float(np.square(transformed[0, LBP_SLICE]).sum()) - 1.0) < 1e-6
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

def test_salient_colour_finds_a_small_vivid_subject() -> None:
    image = Image.new("RGB", (40, 40), (110, 120, 145))
    image.paste(Image.new("RGB", (6, 6), (200, 20, 30)), (17, 17))

    descriptor = extract_features(image)

    assert descriptor.salient_color is not None
    red, green, blue, proportion = descriptor.salient_color.tolist()
    assert red > 0.6 and green < 0.3 and blue < 0.3
    assert proportion == pytest.approx(36 / 1600)


def test_salient_colour_prefers_vivid_accent_over_more_frequent_green() -> None:
    image = Image.new("RGB", (40, 40), (48, 130, 40))
    image.paste(Image.new("RGB", (10, 12), (240, 20, 30)), (15, 14))

    descriptor = extract_features(image)

    assert descriptor.salient_color is not None
    red, green, blue, proportion = descriptor.salient_color.tolist()
    assert red > 0.8 and green < 0.2 and blue < 0.2
    assert proportion == pytest.approx(120 / 1600)


def test_salient_colour_uses_reliable_subject_mask() -> None:
    image = Image.new("RGB", (40, 40), (0, 255, 0))
    image.paste(Image.new("RGB", (16, 16), (220, 90, 90)), (12, 12))

    descriptor = extract_features(image)

    assert descriptor.salient_color is not None
    red, green, blue, proportion = descriptor.salient_color.tolist()
    assert red > 0.75 and green < 0.4 and blue < 0.4
    assert proportion == pytest.approx(256 / 1600)


def test_salient_colour_groups_red_hues_across_hsv_boundary() -> None:
    image = Image.new("RGB", (20, 20))
    image.paste(Image.new("RGB", (10, 20), (255, 0, 16)), (0, 0))
    image.paste(Image.new("RGB", (10, 20), (255, 16, 0)), (10, 0))

    descriptor = extract_features(image)

    assert descriptor.salient_color is not None
    red, green, blue, proportion = descriptor.salient_color.tolist()
    assert red > 0.9 and green < 0.1 and blue < 0.1
    assert proportion == pytest.approx(1.0)


def test_salient_colour_is_absent_on_a_grey_image() -> None:
    descriptor = extract_features(Image.new("RGB", (24, 24), (128, 128, 128)))

    assert descriptor.salient_color is None


def test_salient_colour_does_not_change_the_vector() -> None:
    image = Image.new("RGB", (20, 20), (30, 140, 90))

    descriptor = extract_features(image)

    assert descriptor.vector.shape == (FEATURE_DIMENSION,)
    assert "salient_color" in descriptor.to_dict()
