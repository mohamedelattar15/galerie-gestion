"""Feature extraction endpoints."""

from __future__ import annotations

from typing import Any

from flask import request
from flask_restful import Resource

from backend.routes.auth import login_required
from backend.services.features import extract_uploaded_descriptors

MAX_BATCH_IMAGES = 32


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

        results, failures = extract_uploaded_descriptors(uploads)
        status_code = 207 if failures and len(uploads) > 1 else 400 if failures else 200
        if len(uploads) == 1 and failures:
            return {"error": results[0]["error"]}, status_code
        return {
            "processed": len(uploads) - failures,
            "failed": failures,
            "results": results,
        }, status_code
