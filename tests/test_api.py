import sqlite3
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from flask import Flask
from PIL import Image

from backend.app import create_app
from backend.domain.features import FEATURE_DIMENSION
from backend.services.indexing import build_index


def _png_bytes(color: tuple[int, int, int]) -> bytes:
    stream = BytesIO()
    Image.new("RGB", (16, 16), color).save(stream, format="PNG")
    return stream.getvalue()


def _authenticated_client(app: Flask):
    client = app.test_client()
    response = client.post(
        "/api/auth/register",
        json={"username": "student-g13", "password": "valid-password-123"},
    )
    assert response.status_code == 201
    return client


def _test_config(tmp_path: Path) -> dict[str, Any]:
    return {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE": str(tmp_path / "test.sqlite3"),
        "UPLOAD_DIR": str(tmp_path / "uploads"),
    }


def _make_dataset(root: Path) -> Path:
    dataset = root / "dataset"
    category = dataset / "objects"
    category.mkdir(parents=True)
    for filename, color in (
        ("red.png", (255, 0, 0)),
        ("green.png", (0, 255, 0)),
        ("blue.png", (0, 0, 255)),
    ):
        (category / filename).write_bytes(_png_bytes(color))
    return dataset


def test_health_and_batch_descriptor_extraction(tmp_path: Path) -> None:
    app = create_app(index_path=tmp_path / "missing.npz", config=_test_config(tmp_path))
    client = _authenticated_client(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json == {
        "status": "ok",
        "index_loaded": False,
        "indexed_images": 0,
        "descriptor_modes": [],
    }

    response = client.post(
        "/api/features/extract",
        data={
            "images": [
                (BytesIO(_png_bytes((200, 20, 20))), "first.png"),
                (BytesIO(_png_bytes((20, 200, 20))), "second.png"),
            ]
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.json["processed"] == 2
    assert response.json["failed"] == 0
    assert all(
        result["feature_dimensions"] == FEATURE_DIMENSION
        for result in response.json["results"]
    )


def test_home_page_serves_the_workspace(tmp_path: Path) -> None:
    app = create_app(index_path=tmp_path / "missing.npz", config=_test_config(tmp_path))

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b'<div id="root"></div>' in response.data
    assert b"/static/react/app.css" in response.data
    assert b"/static/react/app.js" in response.data


def test_gallery_descriptors_and_indexed_image_file(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    index_path = tmp_path / "features.npz"
    build_index(dataset, index_path)
    config = _test_config(tmp_path)
    config["DATASET_DIR"] = str(dataset)
    app = create_app(index_path=index_path, config=config)
    client = _authenticated_client(app)

    upload = client.post(
        "/api/images",
        data={"image": (BytesIO(_png_bytes((200, 30, 60))), "flower.png")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    image = upload.json["results"][0]

    descriptors = client.get(f"/api/images/{image['id']}/descriptors")
    assert descriptors.status_code == 200
    assert descriptors.json["feature_dimensions"] == FEATURE_DIMENSION
    assert len(descriptors.json["descriptors"]["color_histogram"]) == 48
    assert len(descriptors.json["descriptors"]["lbp_histogram"]) == 256

    indexed_file = client.get("/api/indexed-images/0/file")
    assert indexed_file.status_code == 200
    assert indexed_file.data.startswith(b"\x89PNG")


def test_batch_descriptor_extraction_reports_invalid_images(tmp_path: Path) -> None:
    app = create_app(index_path=tmp_path / "missing.npz", config=_test_config(tmp_path))
    client = _authenticated_client(app)

    response = client.post(
        "/api/features/extract",
        data={
            "images": [
                (BytesIO(_png_bytes((200, 20, 20))), "valid.png"),
                (BytesIO(b"not an image"), "invalid.png"),
            ]
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 207
    assert response.json["processed"] == 1
    assert response.json["failed"] == 1
    assert "error" in response.json["results"][1]


def test_search_session_persists_across_restarts_and_feedback(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    index_path = tmp_path / "features.npz"
    build_index(dataset, index_path)
    app = create_app(index_path=index_path, config=_test_config(tmp_path))
    client = _authenticated_client(app)

    initial = client.post(
        "/api/search",
        data={
            "query": (BytesIO(_png_bytes((220, 220, 20))), "query.png"),
            "top_k": "3",
        },
        content_type="multipart/form-data",
    )
    assert initial.status_code == 200
    assert len(initial.json["results"]) == 3

    result_ids = [result["id"] for result in initial.json["results"]]
    restarted_app = create_app(index_path=index_path, config=_test_config(tmp_path))
    client = restarted_app.test_client()
    login = client.post(
        "/api/auth/login",
        json={"username": "student-g13", "password": "valid-password-123"},
    )
    assert login.status_code == 200

    feedback = client.post(
        "/api/search/feedback",
        json={
            "session_id": initial.json["session_id"],
            "relevant_ids": result_ids[:2],
            "non_relevant_ids": result_ids[2:],
            "top_k": 3,
        },
    )

    assert feedback.status_code == 200
    assert feedback.json["iteration"] == 1
    assert feedback.json["ignored_non_relevant_count"] == 1
    assert len(feedback.json["weights"]) == FEATURE_DIMENSION
    assert np.isfinite(feedback.json["weights"]).all()
    assert len(feedback.json["results"]) == 3

    next_app = create_app(index_path=index_path, config=_test_config(tmp_path))
    next_client = next_app.test_client()
    assert next_client.post(
        "/api/auth/login",
        json={"username": "student-g13", "password": "valid-password-123"},
    ).status_code == 200
    next_ids = [result["id"] for result in feedback.json["results"]]
    next_feedback = next_client.post(
        "/api/search/feedback",
        json={
            "session_id": initial.json["session_id"],
            "relevant_ids": next_ids[:2],
            "top_k": 3,
        },
    )
    assert next_feedback.status_code == 200
    assert next_feedback.json["iteration"] == 2


def test_feedback_requires_two_relevant_images(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    index_path = tmp_path / "features.npz"
    build_index(dataset, index_path)
    app = create_app(index_path=index_path, config=_test_config(tmp_path))
    client = _authenticated_client(app)

    initial = client.post(
        "/api/search",
        data={
            "query": (BytesIO(_png_bytes((200, 200, 10))), "query.png"),
            "top_k": "3",
        },
        content_type="multipart/form-data",
    )
    one_id = initial.json["results"][0]["id"]

    feedback = client.post(
        "/api/search/feedback",
        json={"session_id": initial.json["session_id"], "relevant_ids": [one_id]},
    )

    assert feedback.status_code == 422
    assert "au moins deux" in feedback.json["error"]


def test_feedback_rejects_a_session_from_a_different_index(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    original_index_path = tmp_path / "original.npz"
    build_index(dataset, original_index_path)
    config = _test_config(tmp_path)
    original_app = create_app(index_path=original_index_path, config=config)
    original_client = _authenticated_client(original_app)
    initial = original_client.post(
        "/api/search",
        data={
            "query": (BytesIO(_png_bytes((220, 220, 20))), "query.png"),
            "top_k": "3",
        },
        content_type="multipart/form-data",
    )
    assert initial.status_code == 200

    (dataset / "objects" / "red.png").write_bytes(_png_bytes((180, 20, 220)))
    changed_index_path = tmp_path / "changed.npz"
    build_index(dataset, changed_index_path)
    changed_app = create_app(index_path=changed_index_path, config=config)
    changed_client = changed_app.test_client()
    assert changed_client.post(
        "/api/auth/login",
        json={"username": "student-g13", "password": "valid-password-123"},
    ).status_code == 200

    result_ids = [result["id"] for result in initial.json["results"]]
    feedback = changed_client.post(
        "/api/search/feedback",
        json={
            "session_id": initial.json["session_id"],
            "relevant_ids": result_ids[:2],
        },
    )

    assert feedback.status_code == 409
    assert "index de recherche a changé" in feedback.json["error"]


def test_authentication_and_gallery_isolation(tmp_path: Path) -> None:
    app = create_app(
        index_path=tmp_path / "missing.npz",
        config=_test_config(tmp_path),
    )
    first_client = app.test_client()
    assert first_client.get("/api/images").status_code == 401
    registered = first_client.post(
        "/api/auth/register",
        json={"username": "student-g13", "password": "valid-password-123"},
    )
    assert registered.status_code == 201
    assert first_client.get("/api/auth/me").status_code == 200
    duplicate = first_client.post(
        "/api/auth/register",
        json={"username": "student-g13", "password": "another-password-123"},
    )
    assert duplicate.status_code == 409

    parent = first_client.post("/api/categories", json={"name": "Nature"})
    assert parent.status_code == 201
    child = first_client.post(
        "/api/categories",
        json={"name": "Flowers", "parent_id": int(parent.json["id"])},
    )
    assert child.status_code == 201
    upload = first_client.post(
        "/api/images",
        data={
            "category_id": str(child.json["id"]),
            "image": (BytesIO(_png_bytes((200, 30, 60))), "flower.png"),
        },
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    original = upload.json["results"][0]
    assert original["category_id"] == child.json["id"]

    download = first_client.get(original["file_url"])
    assert download.status_code == 200
    assert download.data.startswith(b"\x89PNG")
    assert "attachment" not in download.headers["Content-Disposition"]
    download.close()
    attachment = first_client.get(f"{original['file_url']}?download=1")
    assert "attachment" in attachment.headers["Content-Disposition"]
    attachment.close()

    transformed_response = first_client.post(
        f"/api/images/{original['id']}/transform",
        json={"operation": "resize", "width": 8, "height": 8},
    )
    assert transformed_response.status_code == 201
    transformed = transformed_response.json
    assert transformed["parent_image_id"] == original["id"]
    assert (transformed["width"], transformed["height"]) == (8, 8)
    assert transformed["filename"] == "flower_resize_8x8.png"

    chained_response = first_client.post(
        f"/api/images/{transformed['id']}/transform",
        json={"operation": "rotate", "degrees": 90},
    )
    assert chained_response.status_code == 201
    chained = chained_response.json
    assert chained["parent_image_id"] == transformed["id"]
    assert chained["filename"] == "flower_rotate90.png"

    second_client = app.test_client()
    second_registration = second_client.post(
        "/api/auth/register",
        json={"username": "other-user", "password": "another-password-123"},
    )
    assert second_registration.status_code == 201
    assert second_client.get(original["file_url"]).status_code == 404
    assert second_client.get("/api/images").json == {"images": []}

    assert first_client.delete(f"/api/images/{original['id']}").status_code == 409
    assert first_client.delete(f"/api/images/{chained['id']}").status_code == 200
    assert first_client.delete(f"/api/images/{transformed['id']}").status_code == 200
    assert first_client.delete(f"/api/images/{original['id']}").status_code == 200
    assert first_client.delete(f"/api/categories/{child.json['id']}").status_code == 200
    assert first_client.delete(f"/api/categories/{parent.json['id']}").status_code == 200

    assert first_client.post("/api/auth/logout").status_code == 200
    assert first_client.get("/api/auth/me").status_code == 401
    login = first_client.post(
        "/api/auth/login",
        json={"username": "student-g13", "password": "valid-password-123"},
    )
    assert login.status_code == 200
    assert first_client.get("/api/auth/me").status_code == 200


def test_upload_removes_the_stored_file_when_the_database_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(index_path=tmp_path / "missing.npz", config=_test_config(tmp_path))
    client = _authenticated_client(app)
    uploads = tmp_path / "uploads"

    def failing_insert(**_kwargs: Any) -> int:
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr("backend.routes.gallery.insert_image", failing_insert)

    with pytest.raises(sqlite3.OperationalError):
        client.post(
            "/api/images",
            data={"image": (BytesIO(_png_bytes((10, 20, 30))), "orphan.png")},
            content_type="multipart/form-data",
        )

    assert list(uploads.glob("*")) == []


def test_search_accepts_a_gallery_image_as_query(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    index_path = tmp_path / "features.npz"
    build_index(dataset, index_path)
    app = create_app(index_path=index_path, config=_test_config(tmp_path))
    client = _authenticated_client(app)

    upload = client.post(
        "/api/images",
        data={"image": (BytesIO(_png_bytes((220, 220, 20))), "query.png")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    gallery_id = upload.json["results"][0]["id"]

    response = client.post(
        "/api/search",
        data={"gallery_image_id": str(gallery_id), "top_k": "3"},
    )

    assert response.status_code == 200
    assert response.json["query_source"]["type"] == "gallery"
    assert response.json["query_source"]["id"] == gallery_id
    assert response.json["corpus"]["name"] == "GHIM-10K"
    assert response.json["corpus"]["images"] == 3
    assert len(response.json["results"]) == 3


def test_search_rejects_another_users_gallery_image(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    index_path = tmp_path / "features.npz"
    build_index(dataset, index_path)
    app = create_app(index_path=index_path, config=_test_config(tmp_path))
    owner = _authenticated_client(app)
    upload = owner.post(
        "/api/images",
        data={"image": (BytesIO(_png_bytes((10, 200, 30))), "private.png")},
        content_type="multipart/form-data",
    )
    gallery_id = upload.json["results"][0]["id"]

    other = app.test_client()
    assert other.post(
        "/api/auth/register",
        json={"username": "another-g13", "password": "another-password-123"},
    ).status_code == 201

    response = other.post("/api/search", data={"gallery_image_id": str(gallery_id)})

    assert response.status_code == 404
    assert "n'existe pas" in response.json["error"]


def test_search_session_is_private_to_its_owner(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    index_path = tmp_path / "features.npz"
    build_index(dataset, index_path)
    app = create_app(index_path=index_path, config=_test_config(tmp_path))
    owner = _authenticated_client(app)
    initial = owner.post(
        "/api/search",
        data={
            "query": (BytesIO(_png_bytes((220, 220, 20))), "query.png"),
            "top_k": "3",
        },
        content_type="multipart/form-data",
    )
    result_ids = [result["id"] for result in initial.json["results"]]
    other_user = app.test_client()
    registration = other_user.post(
        "/api/auth/register",
        json={"username": "another-g13", "password": "another-password-123"},
    )
    assert registration.status_code == 201

    feedback = other_user.post(
        "/api/search/feedback",
        json={
            "session_id": initial.json["session_id"],
            "relevant_ids": result_ids[:2],
            "top_k": 3,
        },
    )

    assert feedback.status_code == 404
