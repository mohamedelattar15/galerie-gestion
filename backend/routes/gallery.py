"""Authenticated image and category management routes."""

from __future__ import annotations

from io import BytesIO
import re
import sqlite3
from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, jsonify, request, send_file
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from backend.database.repositories.gallery import (
    category_has_contents,
    category_is_owned,
    category_name_exists,
    delete_category as delete_category_record,
    delete_image_record,
    get_owned_category,
    get_owned_image,
    image_has_derived_images,
    insert_category,
    insert_image,
    list_categories as fetch_categories,
    list_images as fetch_images,
)
from backend.domain.features import extract_features
from backend.domain.models import DatasetIndex
from backend.routes.auth import current_user_id, login_required
from backend.services.analysis import analyze_image, render_background_map, render_mask
from backend.services.gallery import apply_transformation
from backend.utils.image_io import (
    MAX_IMAGE_PIXELS,
    FORMAT_MIME_TYPES,
    store_derived_image,
    store_uploaded_image,
    stored_image_path,
)

gallery_api = Blueprint("gallery_api", __name__, url_prefix="/api")
MAX_GALLERY_BATCH = 32


def _image_storage() -> Path:
    return Path(current_app.config["UPLOAD_DIR"])


def _remove_stored_file(stored_name: str | None) -> None:
    if stored_name is None:
        return
    try:
        stored_image_path(_image_storage(), stored_name).unlink(missing_ok=True)
    except (OSError, ValueError):
        current_app.logger.warning("Could not remove stored file %s.", stored_name)


def _derived_filename(
    source: sqlite3.Row,
    image_id: int,
    operation: Any,
    payload: dict[str, Any],
) -> str:
    """Name a derived image after its original, never after another copy.

    Chaining transformations used to stack suffixes
    (``photo_resize_rotate_rotate.png``). The stem is taken from the root
    original and the operation is described once, with its parameters.
    """
    root_name = image_id
    root_stem: str | None = None
    current = source
    for _ in range(64):
        parent_id = current["parent_image_id"]
        if parent_id is None:
            root_stem = Path(str(current["original_filename"])).stem
            root_name = int(current["id"])
            break
        parent = get_owned_image(int(parent_id), int(current["user_id"]))
        if parent is None:
            root_stem = Path(str(current["original_filename"])).stem
            root_name = int(current["id"])
            break
        current = parent

    if root_stem is None:
        root_stem = Path(str(source["original_filename"])).stem
        root_name = image_id

    operation_name = str(operation)
    if operation_name == "rotate":
        operation_name = f"rotate{float(payload.get('degrees', 90)):g}"
    elif operation_name == "flip":
        operation_name = f"flip_{payload.get('direction', 'horizontal')}"
    elif operation_name == "resize":
        operation_name = f"resize_{payload.get('width')}x{payload.get('height')}"
    elif operation_name == "crop":
        box = payload.get("box")
        if "aspect_ratio" in payload:
            operation_name = "crop_" + str(payload["aspect_ratio"]).replace(":", "x")
        elif isinstance(box, list) and len(box) == 4:
            operation_name = "crop_" + "_".join(str(value) for value in box)
    if operation == "rotate" and payload.get("interpolation", "nearest") != "nearest":
        operation_name += f"_{payload['interpolation']}"
    elif operation == "resize" and payload.get("interpolation", "lanczos") != "lanczos":
        operation_name += f"_{payload['interpolation']}"

    if operation in {"brightness", "contrast", "saturation", "sharpness"}:
        operation_name = f"{operation}_{float(payload.get('factor')):g}"
    elif operation in {"blur", "autocontrast"}:
        parameter = "radius" if operation == "blur" else "cutoff"
        operation_name = f"{operation}_{float(payload.get(parameter)):g}"

    base_stem = re.sub(
        r"(_rotate\d*|_flip_[a-z]+|_resize(_\d+x\d+)?|_crop_[-\d_]+)+$",
        "",
        root_stem,
    )
    if not base_stem:
        base_stem = f"image_{root_name}"
    return secure_filename(f"{base_stem}_{operation_name}.png") or "image_derived.png"


def _owned_image(image_id: int) -> sqlite3.Row | None:
    user_id = current_user_id()
    return get_owned_image(image_id, user_id) if user_id is not None else None


def _load_image_for_analysis(
    image_id: int,
) -> tuple[Image.Image | None, tuple[Any, int] | None]:
    row = _owned_image(image_id)
    if row is None:
        return None, (jsonify({"error": "L'image n'existe pas."}), 404)
    try:
        image_path = stored_image_path(_image_storage(), str(row["stored_name"]))
    except ValueError:
        return None, (jsonify({"error": "Le chemin de l'image est invalide."}), 500)
    if not image_path.is_file():
        return None, (jsonify({"error": "Le fichier image associé est introuvable."}), 404)
    try:
        with Image.open(image_path) as opened_image:
            if opened_image.width * opened_image.height > MAX_IMAGE_PIXELS:
                return None, (jsonify({"error": "L'image dépasse la taille maximale autorisée."}), 413)
            opened_image.load()
            return opened_image.copy(), None
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        current_app.logger.exception("Stored image could not be decoded for analysis.")
        return None, (jsonify({"error": "Le fichier image stocké est illisible."}), 500)


def _image_payload(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "category_id": int(row["category_id"]) if row["category_id"] is not None else None,
        "parent_image_id": (
            int(row["parent_image_id"]) if row["parent_image_id"] is not None else None
        ),
        "filename": str(row["original_filename"]),
        "mime_type": str(row["mime_type"]),
        "width": int(row["width"]),
        "height": int(row["height"]),
        "created_at": str(row["created_at"]),
        "file_url": f"/api/images/{int(row['id'])}/file",
    }


def _parse_category_id(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if type(value) is int:
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as error:
            raise ValueError("category_id doit être un nombre entier.") from error
    raise ValueError("category_id doit être un nombre entier.")


@gallery_api.get("/categories")
@login_required
def list_categories() -> tuple[Any, int]:
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401
    rows = fetch_categories(user_id)
    return jsonify(
        [
            {
                "id": int(row["id"]),
                "name": str(row["name"]),
                "parent_id": int(row["parent_id"]) if row["parent_id"] is not None else None,
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]
    ), 200


@gallery_api.post("/categories")
@login_required
def create_category() -> tuple[Any, int]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Le corps de la requête doit être un objet JSON."}), 400
    name = payload.get("name")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        return jsonify({"error": "Le nom de catégorie doit contenir 1 à 100 caractères."}), 400
    try:
        parent_id = _parse_category_id(payload.get("parent_id"))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401
    if parent_id is not None and not category_is_owned(parent_id, user_id):
        return jsonify({"error": "La catégorie parente n'existe pas."}), 404

    normalized_name = name.strip()
    if category_name_exists(user_id, parent_id, normalized_name):
        return jsonify({"error": "Une catégorie de même nom existe déjà à ce niveau."}), 409

    category_id = insert_category(user_id, parent_id, normalized_name)
    return jsonify(
        {
            "id": category_id,
            "name": normalized_name,
            "parent_id": parent_id,
        }
    ), 201


@gallery_api.delete("/categories/<int:category_id>")
@login_required
def delete_category(category_id: int) -> tuple[Any, int]:
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401
    category = get_owned_category(category_id, user_id)
    if category is None:
        return jsonify({"error": "La catégorie n'existe pas."}), 404
    if category_has_contents(category_id, user_id):
        return jsonify({"error": "La catégorie doit être vide avant sa suppression."}), 409
    delete_category_record(category_id, user_id)
    return jsonify({"message": "Catégorie supprimée."}), 200


@gallery_api.route("/images", methods=["GET", "POST"])
@login_required
def images_collection() -> tuple[Any, int]:
    if request.method == "POST":
        return _upload_images()
    return _list_images()


def _upload_images() -> tuple[Any, int]:
    uploads = request.files.getlist("images")
    if not uploads:
        uploads = request.files.getlist("image")
    uploads = [upload for upload in uploads if upload.filename]
    if not uploads:
        return jsonify({"error": "Envoyez un fichier dans le champ 'image' ou 'images'."}), 400
    if len(uploads) > MAX_GALLERY_BATCH:
        return jsonify({"error": f"Un lot ne peut pas dépasser {MAX_GALLERY_BATCH} images."}), 413

    try:
        category_id = _parse_category_id(request.form.get("category_id"))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401
    if category_id is not None and not category_is_owned(category_id, user_id):
        return jsonify({"error": "La catégorie n'existe pas."}), 404

    results: list[dict[str, Any]] = []
    failures = 0
    for upload in uploads:
        stored_name: str | None = None
        try:
            image, image_format, stored_name = store_uploaded_image(upload, _image_storage())
            safe_original_name = secure_filename(upload.filename or "") or "image"
            image_id = insert_image(
                user_id=user_id,
                category_id=category_id,
                parent_image_id=None,
                stored_name=stored_name,
                original_filename=safe_original_name,
                mime_type=FORMAT_MIME_TYPES[image_format],
                width=image.width,
                height=image.height,
            )
            row = _owned_image(image_id)
            if row is None:
                raise RuntimeError("L'image créée ne peut pas être relue.")
            results.append(_image_payload(row))
        except ValueError as error:
            failures += 1
            _remove_stored_file(stored_name)
            results.append({"filename": upload.filename, "error": str(error)})
        except Exception:
            # A database or disk failure must not leave an orphan file behind.
            _remove_stored_file(stored_name)
            raise

    status_code = 207 if failures and len(uploads) > 1 else 400 if failures else 201
    if len(uploads) == 1 and failures:
        return jsonify({"error": results[0]["error"]}), status_code
    return jsonify({"created": len(uploads) - failures, "failed": failures, "results": results}), status_code


def _list_images() -> tuple[Any, int]:
    try:
        limit = int(request.args.get("limit", "50"))
        offset = int(request.args.get("offset", "0"))
        category_id = _parse_category_id(request.args.get("category_id"))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if not 1 <= limit <= 100 or offset < 0:
        return jsonify({"error": "limit doit être entre 1 et 100 et offset doit être positif."}), 400
    sort = request.args.get("sort", "created_desc")
    if sort not in {"created_desc", "created_asc", "name_asc"}:
        return jsonify({"error": "sort doit être created_desc, created_asc ou name_asc."}), 400
    search = request.args.get("q", "").strip()
    if len(search) > 100:
        return jsonify({"error": "La recherche ne peut pas dépasser 100 caractères."}), 400

    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401
    if category_id is not None and not category_is_owned(category_id, user_id):
        return jsonify({"error": "La catégorie n'existe pas."}), 404
    rows = fetch_images(user_id, category_id, limit, offset, sort, search)
    return jsonify({"images": [_image_payload(row) for row in rows]}), 200


@gallery_api.get("/images/<int:image_id>")
@login_required
def get_image(image_id: int) -> tuple[Any, int]:
    image = _owned_image(image_id)
    if image is None:
        return jsonify({"error": "L'image n'existe pas."}), 404
    return jsonify(_image_payload(image)), 200


@gallery_api.get("/images/<int:image_id>/file")
@login_required
def download_image(image_id: int) -> Any:
    image = _owned_image(image_id)
    if image is None:
        return jsonify({"error": "L'image n'existe pas."}), 404
    try:
        image_path = stored_image_path(_image_storage(), str(image["stored_name"]))
    except ValueError as error:
        return jsonify({"error": str(error)}), 500
    if not image_path.is_file():
        return jsonify({"error": "Le fichier image associé est introuvable."}), 404
    return send_file(
        image_path,
        mimetype=str(image["mime_type"]),
        as_attachment=request.args.get("download") == "1",
        download_name=str(image["original_filename"]),
    )


@gallery_api.get("/images/<int:image_id>/descriptors")
@login_required
def image_descriptors(image_id: int) -> tuple[Any, int]:
    image_row = _owned_image(image_id)
    if image_row is None:
        return jsonify({"error": "L'image n'existe pas."}), 404
    image_path = stored_image_path(_image_storage(), str(image_row["stored_name"]))
    if not image_path.is_file():
        return jsonify({"error": "Le fichier image associé est introuvable."}), 404
    try:
        with Image.open(image_path) as opened_image:
            if opened_image.width * opened_image.height > MAX_IMAGE_PIXELS:
                return jsonify({"error": "L'image dépasse la taille maximale autorisée."}), 413
            opened_image.load()
            descriptor = extract_features(opened_image)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        current_app.logger.exception("Stored image could not be decoded.")
        return jsonify({"error": "Le fichier image stocké est illisible."}), 500
    return jsonify(
        {
            "image_id": image_id,
            "feature_dimensions": int(descriptor.vector.size),
            "descriptors": descriptor.to_dict(),
        }
    ), 200


@gallery_api.get("/images/<int:image_id>/analysis")
@login_required
def image_background_analysis(image_id: int) -> Any:
    image, error_response = _load_image_for_analysis(image_id)
    if error_response is not None:
        return error_response
    try:
        analysis = analyze_image(image)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(
        {
            **analysis,
            "background_map_url": f"/api/images/{image_id}/background-map",
            "mask_url": f"/api/images/{image_id}/mask" if analysis["mask_available"] else None,
        }
    ), 200


@gallery_api.get("/images/<int:image_id>/mask")
@login_required
def image_object_mask(image_id: int) -> Any:
    image, error_response = _load_image_for_analysis(image_id)
    if error_response is not None:
        return error_response
    try:
        mask = render_mask(image)
    except ValueError as error:
        return jsonify({"error": str(error)}), 422
    output = BytesIO()
    mask.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png", download_name="mask.png", max_age=0)


@gallery_api.get("/images/<int:image_id>/background-map")
@login_required
def image_background_map(image_id: int) -> Any:
    image, error_response = _load_image_for_analysis(image_id)
    if error_response is not None:
        return error_response
    try:
        background_map = render_background_map(image)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    output = BytesIO()
    background_map.save(output, format="PNG")
    output.seek(0)
    return send_file(
        output,
        mimetype="image/png",
        download_name="background-map.png",
        max_age=0,
    )


@gallery_api.get("/indexed-images/<int:image_id>/file")
@login_required
def indexed_image_file(image_id: int) -> Any:
    index = current_app.extensions["cbir_index"]
    if not isinstance(index, DatasetIndex):
        return jsonify({"error": "Aucun index de recherche n'est chargé."}), 503
    if not 0 <= image_id < len(index.paths):
        return jsonify({"error": "L'identifiant d'image indexée est invalide."}), 404
    dataset_root = Path(current_app.config["DATASET_DIR"]).resolve()
    image_path = (dataset_root / index.paths[image_id]).resolve()
    if not image_path.is_relative_to(dataset_root):
        return jsonify({"error": "Le chemin de l'image indexée est invalide."}), 500
    if not image_path.is_file():
        return jsonify({"error": "Le fichier image indexé est introuvable."}), 404
    return send_file(image_path, as_attachment=False)


@gallery_api.delete("/images/<int:image_id>")
@login_required
def delete_image(image_id: int) -> tuple[Any, int]:
    image = _owned_image(image_id)
    if image is None:
        return jsonify({"error": "L'image n'existe pas."}), 404
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401
    if image_has_derived_images(image_id, user_id):
        return jsonify({"error": "Supprimez d'abord les images dérivées de cette image."}), 409

    image_path = stored_image_path(_image_storage(), str(image["stored_name"]))
    if not image_path.is_file():
        return jsonify({"error": "Le fichier image associé est introuvable."}), 404
    tombstone_path = image_path.with_name(f".{image_path.name}.deleting")
    image_path.replace(tombstone_path)
    try:
        delete_image_record(image_id, user_id)
    except sqlite3.Error:
        tombstone_path.replace(image_path)
        raise
    tombstone_path.unlink()
    return jsonify({"message": "Image supprimée."}), 200


@gallery_api.post("/images/<int:image_id>/transform")
@login_required
def transform_image(image_id: int) -> tuple[Any, int]:
    source = _owned_image(image_id)
    if source is None:
        return jsonify({"error": "L'image n'existe pas."}), 404
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Le corps de la requête doit être un objet JSON."}), 400
    operation = payload.get("operation")
    image_path = stored_image_path(_image_storage(), str(source["stored_name"]))
    if not image_path.is_file():
        return jsonify({"error": "Le fichier image associé est introuvable."}), 404

    try:
        with Image.open(image_path) as opened_image:
            if opened_image.width * opened_image.height > MAX_IMAGE_PIXELS:
                return jsonify({"error": "L'image dépasse la taille maximale autorisée."}), 413
            opened_image.load()
            image = opened_image.copy()
        transformed = apply_transformation(image, operation, payload)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        current_app.logger.exception("Stored image could not be decoded.")
        return jsonify({"error": "Le fichier image stocké est illisible."}), 500
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    stored_name = store_derived_image(transformed, _image_storage())
    original_filename = _derived_filename(source, image_id, operation, payload)
    try:
        derived_id = insert_image(
            user_id=int(source["user_id"]),
            category_id=(
                int(source["category_id"]) if source["category_id"] is not None else None
            ),
            parent_image_id=image_id,
            stored_name=stored_name,
            original_filename=original_filename,
            mime_type="image/png",
            width=transformed.width,
            height=transformed.height,
        )
    except Exception:
        _remove_stored_file(stored_name)
        raise

    derived = _owned_image(derived_id)
    if derived is None:
        raise RuntimeError("L'image dérivée créée ne peut pas être relue.")
    return jsonify(_image_payload(derived)), 201


@gallery_api.post("/images/<int:image_id>/transform/preview")
@login_required
def preview_transformation(image_id: int) -> Any:
    source = _owned_image(image_id)
    if source is None:
        return jsonify({"error": "L'image n'existe pas."}), 404
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Le corps de la requête doit être un objet JSON."}), 400
    image_path = stored_image_path(_image_storage(), str(source["stored_name"]))
    if not image_path.is_file():
        return jsonify({"error": "Le fichier image associé est introuvable."}), 404

    try:
        with Image.open(image_path) as opened_image:
            if opened_image.width * opened_image.height > MAX_IMAGE_PIXELS:
                return jsonify({"error": "L'image dépasse la taille maximale autorisée."}), 413
            opened_image.load()
            transformed = apply_transformation(
                opened_image.copy(), payload.get("operation"), payload
            )
        preview = BytesIO()
        transformed.save(preview, format="PNG")
        preview.seek(0)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        current_app.logger.exception("Stored image could not be decoded for preview.")
        return jsonify({"error": "Le fichier image stocké est illisible."}), 500
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return send_file(preview, mimetype="image/png", download_name="preview.png", max_age=0)
