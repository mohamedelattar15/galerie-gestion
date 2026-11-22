"""Image-processing workflows used by the gallery routes."""

from __future__ import annotations

import math
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from backend.utils.image_io import MAX_IMAGE_PIXELS

MAX_IMAGE_DIMENSION = 4096
INTERPOLATION_METHODS = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}
ASPECT_RATIOS = {"1:1": 1.0, "4:3": 4 / 3, "16:9": 16 / 9}


def _numeric_parameter(
    payload: dict[str, Any],
    name: str,
    minimum: float,
    maximum: float,
) -> float:
    value = payload.get(name)
    if type(value) not in {int, float}:
        raise ValueError(f"{name} doit être un nombre fini.")
    try:
        numeric_value = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{name} doit être un nombre fini.") from error
    if not math.isfinite(numeric_value):
        raise ValueError(f"{name} doit être un nombre fini.")
    if not minimum <= numeric_value <= maximum:
        raise ValueError(f"{name} doit être compris entre {minimum:g} et {maximum:g}.")
    return numeric_value


def _with_original_alpha(original: Image.Image, result: Image.Image) -> Image.Image:
    if "A" in original.getbands():
        result.putalpha(original.getchannel("A"))
    return result


def _interpolation(payload: dict[str, Any], default: str) -> Image.Resampling:
    method = payload.get("interpolation", default)
    if not isinstance(method, str) or method not in INTERPOLATION_METHODS:
        raise ValueError("interpolation doit être nearest, bilinear, bicubic ou lanczos.")
    return INTERPOLATION_METHODS[method]


def _aspect_ratio_crop(image: Image.Image, ratio_name: Any) -> Image.Image:
    if not isinstance(ratio_name, str) or ratio_name not in ASPECT_RATIOS:
        raise ValueError("aspect_ratio doit être 1:1, 4:3 ou 16:9.")
    target_ratio = ASPECT_RATIOS[ratio_name]
    image_ratio = image.width / image.height
    if image_ratio > target_ratio:
        crop_width = max(1, round(image.height * target_ratio))
        left = (image.width - crop_width) // 2
        return image.crop((left, 0, left + crop_width, image.height))
    crop_height = max(1, round(image.width / target_ratio))
    top = (image.height - crop_height) // 2
    return image.crop((0, top, image.width, top + crop_height))


def apply_transformation(
    image: Image.Image,
    operation: Any,
    payload: dict[str, Any],
) -> Image.Image:
    if operation == "crop":
        if "aspect_ratio" in payload:
            result = _aspect_ratio_crop(image, payload.get("aspect_ratio"))
        else:
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
        keep_aspect_ratio = payload.get("keep_aspect_ratio", False)
        if type(keep_aspect_ratio) is not bool:
            raise ValueError("keep_aspect_ratio doit être un booléen.")
        if keep_aspect_ratio:
            scale = min(width / image.width, height / image.height)
            width = max(1, round(image.width * scale))
            height = max(1, round(image.height * scale))
        result = image.resize(
            (width, height),
            _interpolation(payload, "lanczos"),
        )
    elif operation == "rotate":
        degrees = _numeric_parameter(payload, "degrees", -360, 360)
        result = image.rotate(
            degrees,
            resample=_interpolation(payload, "nearest"),
            expand=True,
        )
    elif operation == "flip":
        direction = payload.get("direction")
        if direction == "horizontal":
            result = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif direction == "vertical":
            result = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        else:
            raise ValueError("direction doit être 'horizontal' ou 'vertical'.")
    elif operation in {"brightness", "contrast", "saturation", "sharpness"}:
        factor = _numeric_parameter(payload, "factor", 0.0, 2.0)
        enhancer = {
            "brightness": ImageEnhance.Brightness,
            "contrast": ImageEnhance.Contrast,
            "saturation": ImageEnhance.Color,
            "sharpness": ImageEnhance.Sharpness,
        }[operation]
        result = _with_original_alpha(image, enhancer(image.convert("RGB")).enhance(factor))
    elif operation == "grayscale":
        result = _with_original_alpha(image, image.convert("L").convert("RGB"))
    elif operation == "sepia":
        grayscale = image.convert("L")
        result = _with_original_alpha(
            image,
            ImageOps.colorize(grayscale, black="#3b2416", white="#fff1d6"),
        )
    elif operation == "blur":
        radius = _numeric_parameter(payload, "radius", 0.0, 20.0)
        result = image.filter(ImageFilter.GaussianBlur(radius=radius))
    elif operation == "autocontrast":
        cutoff = _numeric_parameter(payload, "cutoff", 0.0, 10.0)
        result = _with_original_alpha(
            image,
            ImageOps.autocontrast(image.convert("RGB"), cutoff=cutoff),
        )
    else:
        raise ValueError(
            "operation doit être crop, resize, rotate, flip, brightness, contrast, "
            "saturation, sharpness, grayscale, sepia, blur ou autocontrast."
        )

    if result.width * result.height > MAX_IMAGE_PIXELS:
        raise ValueError("La transformation produirait une image trop grande.")
    return result
