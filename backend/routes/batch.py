"""Batch routes for the gallery: delete and move several images at once."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, jsonify, request, send_file

from backend.routes.auth import current_user_id, login_required
from backend.services.batch import (
    BatchError,
    create_images_archive,
    delete_images,
    move_images,
)
from backend.utils.image_io import stored_image_path

batch_api = Blueprint("batch_api", __name__, url_prefix="/api")


def _storage() -> Path:
    return Path(current_app.config["UPLOAD_DIR"])


@batch_api.post("/images/batch-delete")
@login_required
def batch_delete() -> tuple[Any, int]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Le corps de la requête doit être un objet JSON."}), 400
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401
    try:
        report = delete_images(user_id, payload.get("image_ids"), _storage(), stored_image_path)
    except BatchError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(report.as_dict()), 200


@batch_api.post("/images/batch-move")
@login_required
def batch_move() -> tuple[Any, int]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Le corps de la requête doit être un objet JSON."}), 400
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401

    category_id = payload.get("category_id")
    if category_id is not None and type(category_id) is not int:
        return jsonify({"error": "category_id doit être un entier ou null."}), 400
    try:
        report = move_images(user_id, payload.get("image_ids"), category_id)
    except BatchError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(report.as_dict()), 200


@batch_api.post("/images/batch-download")
@login_required
def batch_download() -> Any:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Le corps de la requête doit être un objet JSON."}), 400
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Authentification requise."}), 401

    try:
        archive = create_images_archive(
            user_id,
            payload.get("image_ids"),
            _storage(),
            stored_image_path,
        )
    except BatchError as error:
        return jsonify({"error": str(error)}), error.status_code

    return send_file(
        archive,
        mimetype="application/zip",
        as_attachment=True,
        download_name="galerie-images.zip",
        max_age=0,
    )
