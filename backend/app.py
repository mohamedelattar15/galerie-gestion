"""Flask REST API for descriptors and CBIR/FRE search."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
from flask import Flask, current_app, jsonify, render_template, request
from flask_restful import Api, Resource
from werkzeug.exceptions import RequestEntityTooLarge

from backend.auth import auth_api, current_user_id, login_required
from backend.database import init_db
from backend.features import extract_features
from backend.fre import compute_fre_weights
from backend.gallery import gallery_api
from backend.image_io import load_uploaded_image
from backend.index import DatasetIndex, load_index
from backend.retrieval import SearchSession, rank_index

MAX_BATCH_IMAGES = 32
DEFAULT_TOP_K = 10
MAX_TOP_K = 100


def _get_index() -> DatasetIndex | None:
    index = current_app.extensions["cbir_index"]
    if index is not None and not isinstance(index, DatasetIndex):
        raise RuntimeError("L'index configuré a un type inattendu.")
    return index


def _get_sessions() -> dict[str, SearchSession]:
    sessions = current_app.extensions["search_sessions"]
    if not isinstance(sessions, dict):
        raise RuntimeError("Le stockage des sessions de recherche est invalide.")
    return sessions


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


class HealthResource(Resource):
    def get(self) -> tuple[dict[str, Any], int]:
        index = _get_index()
        return {
            "status": "ok",
            "index_loaded": index is not None,
            "indexed_images": len(index.paths) if index is not None else 0,
        }, 200


class DescriptorResource(Resource):
    method_decorators = [login_required]

    def post(self) -> tuple[dict[str, Any], int]:
        uploads = request.files.getlist("images")
        if not uploads:
            uploads = request.files.getlist("image")
        uploads = [upload for upload in uploads if upload.filename]
        if not uploads:
            return {"error": "Envoyez un fichier dans le champ 'image' ou 'images'."}, 400
        if len(uploads) > MAX_BATCH_IMAGES:
            return {"error": f"Un lot ne peut pas dépasser {MAX_BATCH_IMAGES} images."}, 413

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
                results.append(
                    {
                        "filename": upload.filename,
                        "error": str(error),
                    }
                )

        status_code = 207 if failures and len(uploads) > 1 else 400 if failures else 200
        if len(uploads) == 1 and failures:
            return {"error": results[0]["error"]}, status_code
        return {
            "processed": len(uploads) - failures,
            "failed": failures,
            "results": results,
        }, status_code


class SearchResource(Resource):
    method_decorators = [login_required]

    def post(self) -> tuple[dict[str, Any], int]:
        index = _get_index()
        if index is None:
            return {
                "error": "Aucun index n'est chargé. Construisez-le avec python -m backend.index."
            }, 503

        try:
            top_k = _parse_top_k(request.form.get("top_k", DEFAULT_TOP_K))
        except ValueError as error:
            return {"error": str(error)}, 400

        query_id_value = request.form.get("query_image_id")
        excluded_id: int | None = None
        if query_id_value is not None:
            try:
                excluded_id = int(query_id_value)
            except ValueError:
                return {"error": "query_image_id doit être un nombre entier."}, 400
            if not 0 <= excluded_id < len(index.paths):
                return {"error": "query_image_id ne correspond à aucune image indexée."}, 404
            query_vector = index.vectors[excluded_id]
        else:
            query_upload = request.files.get("query")
            if query_upload is None:
                query_upload = request.files.get("image")
            if query_upload is None:
                return {
                    "error": "Envoyez une image dans le champ 'query' ou un 'query_image_id'."
                }, 400
            try:
                image, _image_format = load_uploaded_image(query_upload)
                raw_vector = extract_features(image).vector
                query_vector = index.normalizer.transform(raw_vector)
            except ValueError as error:
                return {"error": str(error)}, 400

        weights = np.ones(query_vector.size, dtype=np.float32)
        result_ids, distances = rank_index(
            index, query_vector, weights, top_k, excluded_id=excluded_id
        )
        user_id = current_user_id()
        if user_id is None:
            return {"error": "Authentification requise."}, 401
        session_id = uuid4().hex
        _get_sessions()[session_id] = SearchSession(
            owner_user_id=user_id,
            query_vector=query_vector.copy(),
            weights=weights,
            result_ids=result_ids,
            excluded_id=excluded_id,
        )
        return {
            "session_id": session_id,
            "iteration": 0,
            "results": _result_payload(index, result_ids, distances),
        }, 200


class FeedbackResource(Resource):
    method_decorators = [login_required]

    def post(self) -> tuple[dict[str, Any], int]:
        index = _get_index()
        if index is None:
            return {"error": "Aucun index de recherche n'est chargé."}, 503
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return {"error": "Le corps de la requête doit être un objet JSON."}, 400

        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return {"error": "session_id est obligatoire."}, 400
        session = _get_sessions().get(session_id)
        user_id = current_user_id()
        if session is None or user_id is None or session.owner_user_id != user_id:
            return {"error": "La session de recherche n'existe pas ou a expiré."}, 404

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
        if not set(relevant_ids + non_relevant_ids).issubset(session.result_ids):
            return {"error": "Le feedback doit porter sur les résultats de l'itération courante."}, 422
        if len(relevant_ids) < 2:
            return {
                "error": "Sélectionnez au moins deux images pertinentes pour appliquer FRE."
            }, 422

        relevant_vectors = index.vectors[np.asarray(relevant_ids, dtype=np.int64)]
        try:
            weights = compute_fre_weights(relevant_vectors)
        except ValueError as error:
            return {"error": str(error)}, 422
        query_vector = relevant_vectors.mean(axis=0).astype(np.float32)
        result_ids, distances = rank_index(
            index,
            query_vector,
            weights,
            top_k,
            excluded_id=session.excluded_id,
        )

        session.query_vector = query_vector
        session.weights = weights
        session.result_ids = result_ids
        session.iteration += 1
        return {
            "session_id": session_id,
            "iteration": session.iteration,
            "ignored_non_relevant_count": len(non_relevant_ids),
            "weights": weights.tolist(),
            "results": _result_payload(index, result_ids, distances),
        }, 200


def create_app(
    index_path: Path | None = None,
    config: dict[str, Any] | None = None,
) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32),
        DATABASE=os.environ.get(
            "DATABASE_PATH",
            str(Path(app.instance_path) / "cbir.sqlite3"),
        ),
        UPLOAD_DIR=os.environ.get(
            "UPLOAD_DIR",
            str(Path(app.instance_path) / "uploads"),
        ),
        DATASET_DIR=os.environ.get(
            "DATASET_DIR",
            str(Path(__file__).resolve().parent.parent / "GHIM-10K"),
        ),
        MAX_CONTENT_LENGTH=64 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower()
        in {"1", "true", "yes"},
    )
    if config is not None:
        app.config.update(config)
    if not os.environ.get("SECRET_KEY") and (
        config is None or not config.get("SECRET_KEY")
    ):
        app.logger.warning("SECRET_KEY is unset; sessions will expire when the app restarts.")

    init_db(app)
    app.register_blueprint(auth_api)
    app.register_blueprint(gallery_api)
    app.extensions["search_sessions"] = {}

    configured_index = index_path or Path(
        os.environ.get(
            "CBIR_INDEX_PATH",
            Path(__file__).resolve().parent.parent / "instance" / "features.npz",
        )
    )
    app.extensions["cbir_index"] = (
        load_index(configured_index) if configured_index.is_file() else None
    )

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_request(_error: RequestEntityTooLarge) -> tuple[Any, int]:
        return jsonify({"error": "La requête dépasse la taille maximale de 64 Mo."}), 413

    api = Api(app)

    @app.get("/")
    def home() -> str:
        return render_template("index.html")

    api.add_resource(HealthResource, "/health")
    api.add_resource(DescriptorResource, "/api/features/extract")
    api.add_resource(SearchResource, "/api/search")
    api.add_resource(FeedbackResource, "/api/search/feedback")
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
