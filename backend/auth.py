"""Session-based user registration and authentication endpoints."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from backend.database import get_db

auth_api = Blueprint("auth_api", __name__, url_prefix="/api/auth")
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]{3,32}\Z")
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 256


def current_user_id() -> int | None:
    user_id = session.get("user_id")
    return user_id if type(user_id) is int else None


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if current_user_id() is None:
            return jsonify({"error": "Authentification requise."}), 401
        return view(*args, **kwargs)

    return wrapped


@auth_api.post("/register")
def register() -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "Le corps de la requête doit être un objet JSON."}, 400

    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str) or not USERNAME_PATTERN.fullmatch(username):
        return {
            "error": "Le nom d'utilisateur doit contenir 3 à 32 caractères (lettres, chiffres, _, . ou -)."
        }, 400
    if (
        not isinstance(password, str)
        or not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH
    ):
        return {
            "error": f"Le mot de passe doit contenir entre {MIN_PASSWORD_LENGTH} et {MAX_PASSWORD_LENGTH} caractères."
        }, 400

    database = get_db()
    try:
        cursor = database.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        database.commit()
    except sqlite3.IntegrityError:
        return {"error": "Ce nom d'utilisateur est déjà utilisé."}, 409

    user_id = cursor.lastrowid
    if user_id is None:
        raise RuntimeError("La base n'a pas retourné l'identifiant du compte créé.")
    session.clear()
    session["user_id"] = int(user_id)
    session["username"] = username
    current_app.logger.info("A user account was created.")
    return {"id": int(user_id), "username": username}, 201


@auth_api.post("/login")
def login() -> tuple[dict[str, Any], int]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "Le corps de la requête doit être un objet JSON."}, 400
    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return {"error": "username et password sont obligatoires."}, 400

    user = get_db().execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        return {"error": "Nom d'utilisateur ou mot de passe incorrect."}, 401

    session.clear()
    user_id = int(user["id"])
    session["user_id"] = user_id
    session["username"] = str(user["username"])
    return {"id": user_id, "username": str(user["username"])}, 200


@auth_api.post("/logout")
@login_required
def logout() -> tuple[dict[str, Any], int]:
    session.clear()
    return {"message": "Session fermée."}, 200


@auth_api.get("/me")
@login_required
def me() -> tuple[dict[str, Any], int]:
    user_id = current_user_id()
    user = get_db().execute(
        "SELECT id, username FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if user is None:
        session.clear()
        return {"error": "Le compte associé à cette session n'existe plus."}, 401
    return {"id": int(user["id"]), "username": str(user["username"])}, 200
