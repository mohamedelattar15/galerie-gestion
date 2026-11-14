"""Offline CBIR/FRE evaluation using dataset categories as relevance labels."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import numpy as np

from backend.domain.fre import compute_fre_weights
from backend.domain.fre_config import (
    DEFAULT_EPSILON,
    DEFAULT_MINIMUM_RELEVANT,
    DEFAULT_TOP_K,
    FreSettings,
)
from backend.domain.models import DatasetIndex
from backend.domain.retrieval import rank_index
from backend.services.indexing import load_index


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
    top_k: int = DEFAULT_TOP_K,
    feedback_pool: int | None = None,
    feedback_count: int = 5,
    iterations: int = 3,
    seed: int = 42,
    epsilon: float = DEFAULT_EPSILON,
    minimum_relevant: int = DEFAULT_MINIMUM_RELEVANT,
) -> dict[str, Any]:
    """Compare initial retrieval with simulated positive-only FRE feedback.

    By default the simulated user judges exactly the results the interface
    displays (``feedback_pool == top_k``). A larger pool models an oracle and is
    recorded in the report so the two protocols are never confused.
    """
    image_count = len(index.paths)
    if not 1 <= query_count <= image_count:
        raise ValueError(f"query_count doit être compris entre 1 et {image_count}.")
    settings = FreSettings(
        epsilon=epsilon,
        minimum_relevant=minimum_relevant,
        top_k=top_k,
        feedback_pool=feedback_pool,
        feedback_count=feedback_count,
    )
    settings.validate(image_count)
    feedback_pool = settings.resolved_feedback_pool()
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
            if len(relevant_ids) < settings.minimum_relevant:
                skipped_counts[iteration] += 1
            else:
                relevant_vectors = index.vectors[np.asarray(relevant_ids, dtype=np.int64)]
                weights = compute_fre_weights(
                    relevant_vectors,
                    epsilon=settings.epsilon,
                    minimum_relevant=settings.minimum_relevant,
                )
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
            "epsilon": settings.epsilon,
            "minimum_relevant": settings.minimum_relevant,
            "feedback_window_matches_interface": feedback_pool == top_k,
            "feedback_policy": (
                "At each round, select up to feedback_count images with the query's "
                "category among the current feedback_pool results; apply FRE only "
                "when at least minimum_relevant are available. Negative examples are not used."
            ),
        },
        "sampled_query_ids": query_ids,
        "baseline": {
            "precision_at_k": float(baseline[0]),
            "recall_at_k": float(baseline[1]),
        },
        "fre_iterations": iteration_results,
    }


def evaluate_multiple_seeds(
    index: DatasetIndex,
    *,
    seeds: list[int],
    query_count: int = 100,
    top_k: int = DEFAULT_TOP_K,
    feedback_pool: int | None = None,
    feedback_count: int = 5,
    iterations: int = 3,
    epsilon: float = DEFAULT_EPSILON,
    minimum_relevant: int = DEFAULT_MINIMUM_RELEVANT,
) -> dict[str, Any]:
    """Run the same evaluation for several seeds and aggregate run-level metrics."""
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds doit contenir au moins une valeur unique par exécution.")

    reports = [
        evaluate_fre(
            index,
            query_count=query_count,
            top_k=top_k,
            feedback_pool=feedback_pool,
            feedback_count=feedback_count,
            iterations=iterations,
            seed=seed,
            epsilon=epsilon,
            minimum_relevant=minimum_relevant,
        )
        for seed in seeds
    ]

    def summarize(values: list[float]) -> dict[str, float]:
        return {
            "mean": float(np.mean(values)),
            "population_std": float(np.std(values)),
        }
    baseline_summary = {
        metric: summarize([report["baseline"][metric] for report in reports])
        for metric in ("precision_at_k", "recall_at_k")
    }
    iteration_summary = []
    for iteration in range(iterations):
        iteration_summary.append(
            {
                "iteration": iteration + 1,
                **{
                    metric: summarize(
                        [report["fre_iterations"][iteration][metric] for report in reports]
                    )
                    for metric in ("precision_at_k", "recall_at_k")
                },
            }
        )
    protocol = dict(reports[0]["protocol"])
    protocol.pop("seed")
    protocol["seeds"] = seeds
    return {
        "protocol": protocol,
        "runs": reports,
        "mean_and_std_across_seeds": {
            "baseline": baseline_summary,
            "fre_iterations": iteration_summary,
        },
    }


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent.parent
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
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="N pour Precision@N et Recall@N, et nombre de résultats affichés.",
    )
    parser.add_argument(
        "--feedback-pool",
        type=int,
        default=None,
        help=(
            "Nombre de résultats examinés pour simuler les retours. "
            "Par défaut, identique à top_k pour reproduire l'interface; "
            "une valeur supérieure simule un oracle."
        ),
    )
    parser.add_argument(
        "--feedback-count",
        type=int,
        default=5,
        help="Nombre maximal d'exemples positifs par itération.",
    )
    parser.add_argument("--iterations", type=int, default=3, help="Nombre d'itérations FRE.")
    parser.add_argument(
        "--epsilon",
        type=float,
        default=DEFAULT_EPSILON,
        help="Constante epsilon de l'équation (4).",
    )
    parser.add_argument(
        "--minimum-relevant",
        type=int,
        default=DEFAULT_MINIMUM_RELEVANT,
        help="Nombre minimal d'images pertinentes pour appliquer FRE.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Graine du tirage des requêtes.")
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        help="Répéter l'évaluation avec plusieurs graines et agréger les métriques.",
    )
    arguments = parser.parse_args()

    try:
        index = load_index(arguments.index)
        evaluation_parameters = {
            "query_count": arguments.queries,
            "top_k": arguments.top_k,
            "feedback_pool": arguments.feedback_pool,
            "feedback_count": arguments.feedback_count,
            "iterations": arguments.iterations,
            "epsilon": arguments.epsilon,
            "minimum_relevant": arguments.minimum_relevant,
        }
        if arguments.seeds is None:
            report = evaluate_fre(index, seed=arguments.seed, **evaluation_parameters)
        else:
            report = evaluate_multiple_seeds(
                index,
                seeds=arguments.seeds,
                **evaluation_parameters,
            )
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
