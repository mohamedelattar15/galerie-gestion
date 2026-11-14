"""Image-processing workflows used by the gallery routes."""

from __future__ import annotations

from typing import Any

from PIL import Image

from backend.utils.image_io import MAX_IMAGE_PIXELS

MAX_IMAGE_DIMENSION = 4096


def apply_transformation(
    image: Image.Image,
    operation: Any,
    payload: dict[str, Any],
) -> Image.Image:
    if operation == "crop":
        box = payload.get("box")
        if (
            not isinstance(box, list)
            or len(box) != 4
            or any(type(value) is not int for value in box)
        ):
            raise ValueError("box doit contenir quatre coordonnées entières.")
        left, upper, right, lower = box
        if not (0 <= left < right <= image.width and 0 <= upper < lower <= image.height):
            raise ValueError("Les coordonnées de crop doivent être dans les limites de l'image.")
        result = image.crop((left, upper, right, lower))
    elif operation == "resize":
        width = payload.get("width")
        height = payload.get("height")
        if type(width) is not int or type(height) is not int:
            raise ValueError("width et height doivent être des entiers.")
        if not (1 <= width <= MAX_IMAGE_DIMENSION and 1 <= height <= MAX_IMAGE_DIMENSION):
            raise ValueError(
                f"Les dimensions doivent être comprises entre 1 et {MAX_IMAGE_DIMENSION}."
            )
        result = image.resize((width, height), Image.Resampling.LANCZOS)
    elif operation == "rotate":
        degrees = payload.get("degrees")
        if type(degrees) is not int or degrees not in {90, 180, 270}:
            raise ValueError("degrees doit être 90, 180 ou 270 (rotation antihoraire).")
        result = image.rotate(degrees, expand=True)
    elif operation == "flip":
        direction = payload.get("direction")
        if direction == "horizontal":
            result = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif direction == "vertical":
            result = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        else:
            raise ValueError("direction doit être 'horizontal' ou 'vertical'.")
    else:
        raise ValueError("operation doit être crop, resize, rotate ou flip.")

    if result.width * result.height > MAX_IMAGE_PIXELS:
        raise ValueError("La transformation produirait une image trop grande.")
    return result
