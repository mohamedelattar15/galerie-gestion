"""Flask application factory for the CBIR/FRE backend."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template
from flask_restful import Api
from werkzeug.exceptions import RequestEntityTooLarge

from backend.database.connection import init_db
from backend.domain.retrieval import index_fingerprint
from backend.routes.auth import auth_api
from backend.routes.features import DescriptorResource
from backend.routes.gallery import gallery_api
from backend.routes.health import HealthResource
from backend.routes.search import FeedbackResource, SearchResource
from backend.services.indexing import load_index

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTANCE_DIR = PROJECT_ROOT / "instance"


def create_app(
    index_path: Path | None = None,
    config: dict[str, Any] | None = None,
) -> Flask:
    # Pin the instance folder to the repository root so ``python -m backend.app``
    # and ``python backend/app.py`` share the same database and uploads.
    app = Flask(__name__, instance_path=str(INSTANCE_DIR))
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32),
        DATABASE=os.environ.get(
            "DATABASE_PATH",
            str(INSTANCE_DIR / "cbir.sqlite3"),
        ),
        UPLOAD_DIR=os.environ.get(
            "UPLOAD_DIR",
            str(INSTANCE_DIR / "uploads"),
        ),
        DATASET_DIR=os.environ.get(
            "DATASET_DIR",
            str(PROJECT_ROOT / "GHIM-10K"),
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
    configured_index = index_path or Path(
        os.environ.get(
            "CBIR_INDEX_PATH",
            INSTANCE_DIR / "features.npz",
        )
    )
    app.extensions["cbir_index"] = (
        load_index(configured_index) if configured_index.is_file() else None
    )
    app.extensions["cbir_index_fingerprint"] = (
        index_fingerprint(app.extensions["cbir_index"])
        if app.extensions["cbir_index"] is not None
        else None
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
