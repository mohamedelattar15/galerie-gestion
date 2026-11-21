"""Database operations for gallery images and categories."""

from __future__ import annotations

import sqlite3
from typing import Any

from backend.database.connection import get_db


def get_owned_image(image_id: int, user_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT * FROM images WHERE id = ? AND user_id = ?",
        (image_id, user_id),
    ).fetchone()


def category_is_owned(category_id: int, user_id: int) -> bool:
    return (
        get_db()
        .execute(
            "SELECT 1 FROM categories WHERE id = ? AND user_id = ?",
            (category_id, user_id),
        )
        .fetchone()
        is not None
    )


def insert_image(
    *,
    user_id: int,
    category_id: int | None,
    parent_image_id: int | None,
    stored_name: str,
    original_filename: str,
    mime_type: str,
    width: int,
    height: int,
) -> int:
    database = get_db()
    cursor = database.execute(
        """
        INSERT INTO images (
            user_id, category_id, parent_image_id, stored_name,
            original_filename, mime_type, width, height
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            category_id,
            parent_image_id,
            stored_name,
            original_filename,
            mime_type,
            width,
            height,
        ),
    )
    database.commit()
    image_id = cursor.lastrowid
    if image_id is None:
        raise RuntimeError("La base n'a pas retourné l'identifiant de l'image créée.")
    return int(image_id)


def list_categories(user_id: int) -> list[sqlite3.Row]:
    return get_db().execute(
        """
        SELECT id, name, parent_id, created_at
        FROM categories
        WHERE user_id = ?
        ORDER BY COALESCE(parent_id, 0), name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()


def category_name_exists(user_id: int, parent_id: int | None, name: str) -> bool:
    if parent_id is None:
        query = """
            SELECT 1 FROM categories
            WHERE user_id = ? AND parent_id IS NULL AND name = ? COLLATE NOCASE
        """
        parameters: tuple[Any, ...] = (user_id, name)
    else:
        query = """
            SELECT 1 FROM categories
            WHERE user_id = ? AND parent_id = ? AND name = ? COLLATE NOCASE
        """
        parameters = (user_id, parent_id, name)
    return get_db().execute(query, parameters).fetchone() is not None


def insert_category(user_id: int, parent_id: int | None, name: str) -> int:
    database = get_db()
    cursor = database.execute(
        "INSERT INTO categories (user_id, parent_id, name) VALUES (?, ?, ?)",
        (user_id, parent_id, name),
    )
    database.commit()
    category_id = cursor.lastrowid
    if category_id is None:
        raise RuntimeError("La base n'a pas retourné l'identifiant de la catégorie créée.")
    return int(category_id)


def get_owned_category(category_id: int, user_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT id FROM categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    ).fetchone()


def category_has_contents(category_id: int, user_id: int) -> bool:
    database = get_db()
    has_children = database.execute(
        "SELECT 1 FROM categories WHERE parent_id = ? AND user_id = ? LIMIT 1",
        (category_id, user_id),
    ).fetchone()
    has_images = database.execute(
        "SELECT 1 FROM images WHERE category_id = ? AND user_id = ? LIMIT 1",
        (category_id, user_id),
    ).fetchone()
    return has_children is not None or has_images is not None


def delete_category(category_id: int, user_id: int) -> None:
    database = get_db()
    database.execute(
        "DELETE FROM categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    )
    database.commit()


def list_images(
    user_id: int,
    category_id: int | None,
    limit: int,
    offset: int,
) -> list[sqlite3.Row]:
    if category_id is None:
        query = """
            SELECT * FROM images WHERE user_id = ?
            ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?
        """
        parameters: tuple[Any, ...] = (user_id, limit, offset)
    else:
        query = """
            SELECT * FROM images WHERE user_id = ? AND category_id = ?
            ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?
        """
        parameters = (user_id, category_id, limit, offset)
    return get_db().execute(query, parameters).fetchall()


def image_has_derived_images(image_id: int, user_id: int) -> bool:
    return (
        get_db()
        .execute(
            "SELECT 1 FROM images WHERE parent_image_id = ? AND user_id = ? LIMIT 1",
            (image_id, user_id),
        )
        .fetchone()
        is not None
    )


def delete_image_record(image_id: int, user_id: int) -> None:
    database = get_db()
    database.execute(
        "DELETE FROM images WHERE id = ? AND user_id = ?",
        (image_id, user_id),
    )
    database.commit()


def images_with_derived(user_id: int, image_ids: list[int]) -> set[int]:
    """Return the subset of ``image_ids`` that still have derived copies."""
    if not image_ids:
        return set()
    placeholders = ",".join("?" for _ in image_ids)
    rows = get_db().execute(
        f"""
        SELECT DISTINCT parent_image_id FROM images
        WHERE user_id = ? AND parent_image_id IN ({placeholders})
        """,
        (user_id, *image_ids),
    ).fetchall()
    return {int(row["parent_image_id"]) for row in rows}


def owned_image_records(user_id: int, image_ids: list[int]) -> dict[int, sqlite3.Row]:
    """Return the owned image rows for the given identifiers, keyed by id."""
    if not image_ids:
        return {}
    placeholders = ",".join("?" for _ in image_ids)
    rows = get_db().execute(
        f"SELECT * FROM images WHERE user_id = ? AND id IN ({placeholders})",
        (user_id, *image_ids),
    ).fetchall()
    return {int(row["id"]): row for row in rows}


def move_images_to_category(user_id: int, image_ids: list[int], category_id: int | None) -> int:
    """Reassign several images to a category and return the number of rows touched."""
    if not image_ids:
        return 0
    placeholders = ",".join("?" for _ in image_ids)
    database = get_db()
    cursor = database.execute(
        f"""
        UPDATE images SET category_id = ?
        WHERE user_id = ? AND id IN ({placeholders})
        """,
        (category_id, user_id, *image_ids),
    )
    database.commit()
    return cursor.rowcount
