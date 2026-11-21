"""Batch operations on gallery images.

Deleting or moving several images at once keeps the per-image rules of the
single-image endpoints: an image that still has derived copies cannot be
deleted, and every identifier must belong to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from backend.database.repositories.gallery import (
    category_is_owned,
    delete_image_record,
    images_with_derived,
    move_images_to_category,
    owned_image_records,
)

MAX_BATCH_SIZE = 100


class BatchError(ValueError):
    """A batch request that cannot be executed at all."""


@dataclass
class BatchReport:
    succeeded: list[int] = field(default_factory=list)
    failed: list[dict[str, object]] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {"succeeded": self.succeeded, "failed": self.failed}


def _validate_ids(image_ids: object) -> list[int]:
    if not isinstance(image_ids, list) or not image_ids:
        raise BatchError("image_ids doit être une liste non vide.")
    if any(type(value) is not int for value in image_ids):
        raise BatchError("Les identifiants d'images doivent être des entiers.")
    if len(set(image_ids)) != len(image_ids):
        raise BatchError("La liste ne doit pas contenir de doublons.")
    if len(image_ids) > MAX_BATCH_SIZE:
        raise BatchError(f"Un lot ne peut pas dépasser {MAX_BATCH_SIZE} images.")
    return image_ids


def delete_images(
    user_id: int,
    image_ids: object,
    storage_dir: Path,
    stored_path: Callable[[Path, str], Path],
) -> BatchReport:
    """Delete several images, reporting each outcome.

    A blocked or missing image does not abort the batch; it is reported in the
    ``failed`` list so the interface can explain what happened.
    """
    identifiers = _validate_ids(image_ids)
    owned = owned_image_records(user_id, identifiers)
    blocked = images_with_derived(user_id, identifiers)
    report = BatchReport()

    for image_id in identifiers:
        row = owned.get(image_id)
        if row is None:
            report.failed.append({"id": image_id, "reason": "L'image n'existe pas."})
            continue
        if image_id in blocked:
            report.failed.append(
                {
                    "id": image_id,
                    "reason": "Supprimez d'abord les images dérivées de cette image.",
                }
            )
            continue

        stored_name = str(row["stored_name"])
        try:
            image_path = stored_path(storage_dir, stored_name)
        except ValueError:
            report.failed.append({"id": image_id, "reason": "Le chemin de stockage est invalide."})
            continue
        if not image_path.is_file():
            report.failed.append(
                {"id": image_id, "reason": "Le fichier image associé est introuvable."}
            )
            continue

        tombstone = image_path.with_name(f".{image_path.name}.deleting")
        image_path.replace(tombstone)
        try:
            delete_image_record(image_id, user_id)
        except Exception:
            tombstone.replace(image_path)
            raise
        tombstone.unlink()
        report.succeeded.append(image_id)

    return report


def move_images(
    user_id: int,
    image_ids: object,
    category_id: int | None,
) -> BatchReport:
    """Move several images to a category, reporting each outcome."""
    identifiers = _validate_ids(image_ids)
    if category_id is not None and not category_is_owned(category_id, user_id):
        raise BatchError("La catégorie n'existe pas.")

    owned = owned_image_records(user_id, identifiers)
    report = BatchReport()
    movable = [image_id for image_id in identifiers if image_id in owned]
    for image_id in identifiers:
        if image_id not in owned:
            report.failed.append({"id": image_id, "reason": "L'image n'existe pas."})

    if movable:
        move_images_to_category(user_id, movable, category_id)
        report.succeeded.extend(movable)
    return report
