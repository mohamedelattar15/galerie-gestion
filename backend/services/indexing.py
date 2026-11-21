"""Build and load a precomputed feature index for an image dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from backend.domain.features import FEATURE_DIMENSION, extract_features
from backend.domain.models import DatasetIndex
from backend.domain.normalization import FeatureNormalizer

SUPPORTED_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}


def _image_files(dataset_dir: Path) -> list[Path]:
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"Le dossier du dataset n'existe pas : {dataset_dir}")
    return sorted(
        path
        for path in dataset_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def build_index(dataset_dir: Path, output_path: Path) -> DatasetIndex:
    """Extract all supported images and write a compressed NumPy index."""
    root = dataset_dir.resolve()
    image_paths = _image_files(root)
    if not image_paths:
        raise ValueError(f"Aucune image prise en charge dans {root}")

    raw_vectors: list[NDArray[np.float32]] = []
    relative_paths: list[str] = []
    labels: list[str] = []
    for path in image_paths:
        with Image.open(path) as image:
            descriptor = extract_features(image)
        raw_vectors.append(descriptor.vector)
        relative_path = path.relative_to(root)
        relative_paths.append(relative_path.as_posix())
        labels.append(relative_path.parts[0] if len(relative_path.parts) > 1 else "uncategorized")

    raw_matrix = np.stack(raw_vectors).astype(np.float32)
    normalizer = FeatureNormalizer.fit(raw_matrix)
    normalized_matrix = normalizer.transform(raw_matrix)
    if normalized_matrix.shape != (len(relative_paths), FEATURE_DIMENSION):
        raise RuntimeError("L'index créé a une forme inattendue.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(output_path.name + ".tmp")
    try:
        with temporary_path.open("wb") as output_file:
            np.savez_compressed(
                output_file,
                paths=np.asarray(relative_paths, dtype=np.str_),
                labels=np.asarray(labels, dtype=np.str_),
                vectors=normalized_matrix,
                mean=normalizer.mean,
                scale=normalizer.scale,
            )
        temporary_path.replace(output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    return DatasetIndex(
        paths=tuple(relative_paths),
        labels=tuple(labels),
        vectors=normalized_matrix,
        normalizer=normalizer,
    )


def load_index(index_path: Path) -> DatasetIndex:
    if not index_path.is_file():
        raise FileNotFoundError(f"Le fichier d'index n'existe pas : {index_path}")
    with np.load(index_path, allow_pickle=False) as saved:
        paths = tuple(str(value) for value in saved["paths"].tolist())
        labels = tuple(str(value) for value in saved["labels"].tolist())
        vectors = np.asarray(saved["vectors"], dtype=np.float32)
        mean = np.asarray(saved["mean"], dtype=np.float32)
        scale = np.asarray(saved["scale"], dtype=np.float32)

    if vectors.ndim != 2 or vectors.shape != (len(paths), FEATURE_DIMENSION):
        raise ValueError("Le fichier d'index contient des vecteurs de dimensions invalides.")
    if len(labels) != len(paths) or len(paths) == 0:
        raise ValueError("Le fichier d'index contient des métadonnées invalides.")
    if mean.shape != scale.shape or not np.isfinite(vectors).all():
        raise ValueError("Le fichier d'index contient des valeurs invalides.")
    if np.any(scale <= 0) or not np.isfinite(mean).all() or not np.isfinite(scale).all():
        raise ValueError("Les paramètres de normalisation de l'index sont invalides.")
    return DatasetIndex(paths, labels, vectors, FeatureNormalizer(mean, scale))


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent.parent
    parser = argparse.ArgumentParser(description="Pré-calculer les descripteurs du dataset.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=project_root / "GHIM-10K",
        help="Dossier contenant une image par fichier et une catégorie par sous-dossier.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "instance" / "features.npz",
        help="Chemin du fichier d'index compressé.",
    )
    arguments = parser.parse_args()
    index = build_index(arguments.dataset, arguments.output)
    print(f"Index créé : {len(index.paths)} images, {FEATURE_DIMENSION} dimensions.")
    print(f"Fichier : {arguments.output}")


if __name__ == "__main__":
    main()
