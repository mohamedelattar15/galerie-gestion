"""CBIR search and relevance-feedback endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from flask import current_app, request
from flask_restful import Resource
from PIL import Image, UnidentifiedImageError

from backend.database.repositories.gallery import get_owned_image
from backend.domain.features import extract_features
from backend.domain.models import DatasetIndex
from backend.domain.retrieval import index_fingerprint
from backend.routes.auth import current_user_id, login_required
from backend.services.search import (
    SearchServiceError,
    apply_feedback,
    load_feedback_session,
    start_search,
)
from backend.utils.image_io import load_uploaded_image

DEFAULT_TOP_K = 10
MAX_TOP_K = 100


def _get_index(mode: str = "global") -> DatasetIndex | None:
    variants = current_app.extensions.get("cbir_indexes") or {}
    index = variants.get(mode)
    if index is None:
        index = current_app.extensions["cbir_index"]
    if index is not None and not isinstance(index, DatasetIndex):
        raise RuntimeError("L'index configuré a un type inattendu.")
    return index


def _available_modes() -> list[str]:
    variants = current_app.extensions.get("cbir_indexes") or {}
    return [mode for mode in ("global", "variance", "adaptive") if mode in variants]


def _fingerprint_for(index: DatasetIndex, mode: str) -> str:
    fingerprints = current_app.extensions.setdefault("cbir_index_fingerprints", {})
    if mode not in fingerprints:
        fingerprints[mode] = index_fingerprint(index)
    return fingerprints[mode]


def _parse_top_k(value: Any) -> int:
    try:
        top_k = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("top_k doit être un nombre entier.") from error
    if not 1 <= top_k <= MAX_TOP_K:
        raise ValueError(f"top_k doit être compris entre 1 et {MAX_TOP_K}.")
    return top_k


def _result_payload(
    index: DatasetIndex,
    result_ids: list[int],
    distances: np.ndarray,
) -> list[dict[str, Any]]:
    return [
        {
            "id": image_id,
            "path": index.paths[image_id],
            "category": index.labels[image_id],
            "distance": float(distances[image_id]),
        }
        for image_id in result_ids
    ]


class SearchResource(Resource):
    method_decorators = [login_required]

    def post(self) -> tuple[dict[str, Any], int]:
        requested_mode = request.form.get("descriptor_mode", "global")
        if requested_mode not in _available_modes():
            requested_mode = "global"
        index = _get_index(requested_mode)
        if index is None:
            return {
                "error": "Aucun index n'est chargé. Construisez-le avec python -m backend.services.indexing."
            }, 503

        try:
            top_k = _parse_top_k(request.form.get("top_k", DEFAULT_TOP_K))
        except ValueError as error:
            return {"error": str(error)}, 400

        query_id_value = request.form.get("query_image_id")
        gallery_image_id = request.form.get("gallery_image_id")
        excluded_id: int | None = None
        query_source: dict[str, Any] | None = None
        if query_id_value is not None:
            try:
                excluded_id = int(query_id_value)
            except ValueError:
                return {"error": "query_image_id doit être un nombre entier."}, 400
            if not 0 <= excluded_id < len(index.paths):
                return {"error": "query_image_id ne correspond à aucune image indexée."}, 404
            query_vector = index.vectors[excluded_id]
            query_source = {
                "type": "index",
                "id": excluded_id,
                "path": index.paths[excluded_id],
                "category": index.labels[excluded_id],
                "file_url": f"/api/indexed-images/{excluded_id}/file",
            }
        elif gallery_image_id is not None:
            user_id = current_user_id()
            if user_id is None:
                return {"error": "Authentification requise."}, 401
            try:
                gallery_id = int(gallery_image_id)
            except ValueError:
                return {"error": "gallery_image_id doit être un nombre entier."}, 400
            row = get_owned_image(gallery_id, user_id)
            if row is None:
                return {"error": "L'image de galerie n'existe pas."}, 404
            try:
                query_vector = _vector_from_stored_image(
                    index, Path(str(row["stored_name"]))
                )
            except ValueError as error:
                return {"error": str(error)}, 400
            query_source = {
                "type": "gallery",
                "id": gallery_id,
                "filename": str(row["original_filename"]),
                "file_url": f"/api/images/{gallery_id}/file",
            }
        else:
            query_upload = request.files.get("query")
            if query_upload is None:
                query_upload = request.files.get("image")
            if query_upload is None:
                return {
                    "error": (
                        "Envoyez une image dans le champ 'query', un 'query_image_id' "
                        "ou un 'gallery_image_id'."
                    )
                }, 400
            try:
                image, _image_format = load_uploaded_image(query_upload)
                raw_vector = extract_features(image, mode=requested_mode).vector
                query_vector = index.normalizer.transform(raw_vector)
            except ValueError as error:
                return {"error": str(error)}, 400
            query_source = {
                "type": "upload",
                "filename": query_upload.filename,
            }

        user_id = current_user_id()
        if user_id is None:
            return {"error": "Authentification requise."}, 401
        current_fingerprint = _fingerprint_for(index, requested_mode)
        session_id, result_ids, distances = start_search(
            index,
            query_vector,
            top_k,
            user_id,
            current_fingerprint,
            excluded_id=excluded_id,
        )
        return {
            "session_id": session_id,
            "iteration": 0,
            "descriptor_mode": requested_mode,
            "available_modes": _available_modes(),
            "query_source": query_source,
            "corpus": {
                "name": "GHIM-10K",
                "images": len(index.paths),
                "categories": len(set(index.labels)),
            },
            "results": _result_payload(index, result_ids, distances),
        }, 200


def _vector_from_stored_image(
    index: DatasetIndex,
    stored_name: Path,
) -> np.ndarray:
    """Extract and normalize the descriptor vector of a stored gallery image."""
    from backend.routes.gallery import _image_storage  # local to avoid a cycle
    from backend.utils.image_io import MAX_IMAGE_PIXELS, stored_image_path

    image_path = stored_image_path(_image_storage(), stored_name.name)
    if not image_path.is_file():
        raise ValueError("Le fichier image associé est introuvable.")
    try:
        with Image.open(image_path) as opened_image:
            if opened_image.width * opened_image.height > MAX_IMAGE_PIXELS:
                raise ValueError("L'image dépasse la taille maximale autorisée.")
            opened_image.load()
            raw_vector = extract_features(opened_image).vector
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        raise ValueError("Le fichier image stocké est illisible.") from error
    return index.normalizer.transform(raw_vector)


class FeedbackResource(Resource):
    method_decorators = [login_required]

    def post(self) -> tuple[dict[str, Any], int]:
        payload = request.get_json(silent=True)
        requested_mode = payload.get("descriptor_mode") if isinstance(payload, dict) else None
        if not isinstance(requested_mode, str) or requested_mode not in _available_modes():
            requested_mode = "global"
        index = _get_index(requested_mode)
        if index is None:
            return {"error": "Aucun index de recherche n'est chargé."}, 503
        if not isinstance(payload, dict):
            return {"error": "Le corps de la requête doit être un objet JSON."}, 400

        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return {"error": "session_id est obligatoire."}, 400
        user_id = current_user_id()
        if user_id is None:
            return {"error": "Authentification requise."}, 401
        current_fingerprint = _fingerprint_for(index, requested_mode)
        try:
            session = load_feedback_session(session_id, user_id, current_fingerprint)
        except SearchServiceError as error:
            return {"error": str(error)}, error.status_code

        try:
            top_k = _parse_top_k(payload.get("top_k", DEFAULT_TOP_K))
        except ValueError as error:
            return {"error": str(error)}, 400

        relevant_ids = payload.get("relevant_ids")
        non_relevant_ids = payload.get("non_relevant_ids", [])
        if not isinstance(relevant_ids, list) or not isinstance(non_relevant_ids, list):
            return {"error": "relevant_ids et non_relevant_ids doivent être des listes."}, 400
        if any(type(value) is not int for value in relevant_ids + non_relevant_ids):
            return {"error": "Les identifiants d'images doivent être des entiers."}, 400
        if len(set(relevant_ids)) != len(relevant_ids) or len(set(non_relevant_ids)) != len(non_relevant_ids):
            return {"error": "Les listes de feedback ne doivent pas contenir de doublons."}, 400
        if set(relevant_ids).intersection(non_relevant_ids):
            return {"error": "Une image ne peut pas être à la fois pertinente et non pertinente."}, 400

        try:
            session, distances = apply_feedback(
                index,
                session_id,
                session,
                relevant_ids,
                non_relevant_ids,
                top_k,
            )
        except SearchServiceError as error:
            return {"error": str(error)}, error.status_code
        return {
            "session_id": session_id,
            "iteration": session.iteration,
            "descriptor_mode": requested_mode,
            "ignored_non_relevant_count": len(non_relevant_ids),
            "weights": session.weights.tolist(),
            "results": _result_payload(index, session.result_ids, distances),
        }, 200
