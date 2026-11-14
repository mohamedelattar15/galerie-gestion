"""Offline CBIR/FRE evaluation using dataset categories as relevance labels."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import numpy as np

from backend.fre import compute_fre_weights
from backend.index import DatasetIndex, load_index
from backend.retrieval import rank_index


def _precision_recall(
    result_ids: list[int],
    labels: tuple[str, ...],
    query_id: int,
    top_k: int,
) -> tuple[float, float]:
    query_label = labels[query_id]
    relevant_count = sum(label == query_label for label in labels) - 1
    hits = sum(labels[image_id] == query_label for image_id in result_ids[:top_k])
    recall = hits / relevant_count if relevant_count > 0 else 0.0
    return hits / top_k, recall


def evaluate_fre(
    index: DatasetIndex,
    *,
    query_count: int = 100,
    top_k: int = 10,
    feedback_pool: int = 50,
    feedback_count: int = 5,
    iterations: int = 3,
    seed: int = 42,
) -> dict[str, Any]:
    """Compare initial retrieval with simulated positive-only FRE feedback."""
    image_count = len(index.paths)
    if not 1 <= query_count <= image_count:
        raise ValueError(f"query_count doit être compris entre 1 et {image_count}.")
    if not 1 <= top_k < image_count:
        raise ValueError(f"top_k doit être compris entre 1 et {image_count - 1}.")
    if not top_k <= feedback_pool < image_count:
        raise ValueError("feedback_pool doit être entre top_k et le nombre d'images moins un.")
    if not 2 <= feedback_count <= feedback_pool:
        raise ValueError("feedback_count doit être entre 2 et feedback_pool.")
    if iterations < 1:
        raise ValueError("iterations doit être supérieur ou égal à 1.")

    query_ids = random.Random(seed).sample(range(image_count), query_count)
    baseline_totals = np.zeros(2, dtype=np.float64)
    iteration_totals = np.zeros((iterations, 2), dtype=np.float64)
    applied_counts = [0] * iterations
    skipped_counts = [0] * iterations

    for query_id in query_ids:
        query_label = index.labels[query_id]
        query_vector = index.vectors[query_id].copy()
        weights = np.ones(query_vector.size, dtype=np.float32)
        result_ids, _distances = rank_index(
            index, query_vector, weights, feedback_pool, excluded_id=query_id
        )
        baseline_totals += _precision_recall(result_ids, index.labels, query_id, top_k)

        for iteration in range(iterations):
            relevant_ids = [
                image_id
                for image_id in result_ids[:feedback_pool]
                if index.labels[image_id] == query_label
            ][:feedback_count]
            if len(relevant_ids) < 2:
                skipped_counts[iteration] += 1
            else:
                relevant_vectors = index.vectors[np.asarray(relevant_ids, dtype=np.int64)]
                weights = compute_fre_weights(relevant_vectors)
                query_vector = relevant_vectors.mean(axis=0).astype(np.float32)
                result_ids, _distances = rank_index(
                    index,
                    query_vector,
                    weights,
                    feedback_pool,
                    excluded_id=query_id,
                )
                applied_counts[iteration] += 1
            iteration_totals[iteration] += _precision_recall(
                result_ids, index.labels, query_id, top_k
            )

    baseline = baseline_totals / query_count
    iteration_results = []
    for iteration in range(iterations):
        metrics = iteration_totals[iteration] / query_count
        iteration_results.append(
            {
                "iteration": iteration + 1,
                "precision_at_k": float(metrics[0]),
                "recall_at_k": float(metrics[1]),
                "feedback_applied": applied_counts[iteration],
                "feedback_skipped": skipped_counts[iteration],
            }
        )

    return {
        "protocol": {
            "queries": query_count,
            "top_k": top_k,
            "feedback_pool": feedback_pool,
            "feedback_count": feedback_count,
            "iterations": iterations,
            "seed": seed,
            "feedback_policy": (
                "At each round, select up to feedback_count images with the query's "
                "category among the current feedback_pool results; apply FRE only "
                "when at least two are available. Negative examples are not used."
            ),
        },
        "sampled_query_ids": query_ids,
        "baseline": {
            "precision_at_k": float(baseline[0]),
            "recall_at_k": float(baseline[1]),
        },
        "fre_iterations": iteration_results,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Comparer CBIR et FRE hors ligne sur les catégories de GHIM-10K."
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=project_root / "instance" / "features.npz",
        help="Fichier d'index pré-calculé.",
    )
    parser.add_argument("--queries", type=int, default=100, help="Nombre de requêtes tirées.")
    parser.add_argument("--top-k", type=int, default=10, help="N pour Precision@N et Recall@N.")
    parser.add_argument(
        "--feedback-pool",
        type=int,
        default=50,
        help="Nombre de résultats examinés pour simuler les retours.",
    )
    parser.add_argument(
        "--feedback-count",
        type=int,
        default=5,
        help="Nombre maximal d'exemples positifs par itération.",
    )
    parser.add_argument("--iterations", type=int, default=3, help="Nombre d'itérations FRE.")
    parser.add_argument("--seed", type=int, default=42, help="Graine du tirage des requêtes.")
    arguments = parser.parse_args()

    try:
        index = load_index(arguments.index)
        report = evaluate_fre(
            index,
            query_count=arguments.queries,
            top_k=arguments.top_k,
            feedback_pool=arguments.feedback_pool,
            feedback_count=arguments.feedback_count,
            iterations=arguments.iterations,
            seed=arguments.seed,
        )
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
