"""Application services for image feature extraction."""

from __future__ import annotations

from typing import Any

from backend.domain.features import extract_features
from backend.utils.image_io import load_uploaded_image


def extract_uploaded_descriptors(uploads: list[Any]) -> tuple[list[dict[str, Any]], int]:
    results: list[dict[str, Any]] = []
    failures = 0
    for upload in uploads:
        try:
            image, _image_format = load_uploaded_image(upload)
            descriptor = extract_features(image)
            results.append(
                {
                    "filename": upload.filename,
                    "feature_dimensions": int(descriptor.vector.size),
                    "descriptors": descriptor.to_dict(),
                }
            )
        except ValueError as error:
            failures += 1
            results.append({"filename": upload.filename, "error": str(error)})
    return results, failures
