"""Validation and safe storage helpers for uploaded image files."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

MAX_IMAGE_PIXELS = 40_000_000
FORMAT_EXTENSIONS = {
    "BMP": ".bmp",
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}
FORMAT_MIME_TYPES = {
    "BMP": "image/bmp",
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


def load_uploaded_image(upload: FileStorage) -> tuple[Image.Image, str]:
    if not upload.filename:
        raise ValueError("Le fichier ne possède pas de nom.")
    try:
        with Image.open(upload.stream) as opened_image:
            image_format = opened_image.format
            if image_format not in FORMAT_EXTENSIONS:
                raise ValueError("Format accepté : BMP, JPEG, PNG ou WEBP.")
            if opened_image.width * opened_image.height > MAX_IMAGE_PIXELS:
                raise ValueError("L'image dépasse la taille maximale autorisée.")
            opened_image.load()
            return opened_image.copy(), image_format
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        raise ValueError("Le fichier envoyé n'est pas une image valide.") from error


def store_uploaded_image(
    upload: FileStorage,
    storage_dir: Path,
) -> tuple[Image.Image, str, str]:
    image, image_format = load_uploaded_image(upload)
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{FORMAT_EXTENSIONS[image_format]}"
    destination = storage_dir / stored_name
    upload.stream.seek(0)
    destination.write_bytes(upload.stream.read())
    return image, image_format, stored_name


def store_derived_image(image: Image.Image, storage_dir: Path) -> str:
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}.png"
    destination = storage_dir / stored_name
    prepared = image.convert("RGBA" if "A" in image.getbands() else "RGB")
    prepared.save(destination, format="PNG")
    return stored_name


def stored_image_path(storage_dir: Path, stored_name: str) -> Path:
    path = (storage_dir / stored_name).resolve()
    root = storage_dir.resolve()
    if path.parent != root:
        raise ValueError("Le chemin de stockage de l'image est invalide.")
    return path
