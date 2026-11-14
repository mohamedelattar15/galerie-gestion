"""Database operations for user accounts."""

from __future__ import annotations

import sqlite3

from backend.database.connection import get_db


class DuplicateUsernameError(ValueError):
    """Raised when an account username is already registered."""


def create_user(username: str, password_hash: str) -> int:
    database = get_db()
    try:
        cursor = database.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        database.commit()
    except sqlite3.IntegrityError as error:
        raise DuplicateUsernameError from error
    user_id = cursor.lastrowid
    if user_id is None:
        raise RuntimeError("La base n'a pas retourné l'identifiant du compte créé.")
    return int(user_id)


def get_user_by_username(username: str) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT id, username FROM users WHERE id = ?", (user_id,)
    ).fetchone()
