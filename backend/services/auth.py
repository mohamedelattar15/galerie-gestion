"""Application services for user authentication."""

from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

from backend.database.repositories.users import (
    create_user,
    get_user_by_id,
    get_user_by_username,
)


def register_user(username: str, password: str) -> int:
    return create_user(username, generate_password_hash(password))


def authenticate_user(username: str, password: str) -> tuple[int, str] | None:
    user = get_user_by_username(username.strip())
    if user is None or not check_password_hash(user["password_hash"], password):
        return None
    return int(user["id"]), str(user["username"])


def find_user(user_id: int) -> tuple[int, str] | None:
    user = get_user_by_id(user_id)
    if user is None:
        return None
    return int(user["id"]), str(user["username"])
