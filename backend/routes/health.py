"""Health-check endpoint."""

from __future__ import annotations

from typing import Any

from flask import current_app
from flask_restful import Resource

from backend.domain.models import DatasetIndex


class HealthResource(Resource):
    def get(self) -> tuple[dict[str, Any], int]:
        index = current_app.extensions["cbir_index"]
        if index is not None and not isinstance(index, DatasetIndex):
            raise RuntimeError("L'index configuré a un type inattendu.")
        return {
            "status": "ok",
            "index_loaded": index is not None,
            "indexed_images": len(index.paths) if index is not None else 0,
        }, 200
