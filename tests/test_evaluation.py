from pathlib import Path

from PIL import Image

from backend.evaluation import evaluate_fre
from backend.index import build_index


def _make_dataset(root: Path, categories: dict[str, list[tuple[int, int, int]]]) -> Path:
    dataset = root / "dataset"
    for category_name, colors in categories.items():
        category = dataset / category_name
        category.mkdir(parents=True)
        for index, color in enumerate(colors):
            Image.new("RGB", (16, 16), color).save(category / f"{index}.png")
    return dataset


def test_evaluate_fre_reports_baseline_and_iterations(tmp_path: Path) -> None:
    dataset = _make_dataset(
        tmp_path,
        {"objects": [(255, 0, 0), (0, 255, 0), (0, 0, 255)]},
    )
    index = build_index(dataset, tmp_path / "features.npz")

    report = evaluate_fre(
        index,
        query_count=3,
        top_k=1,
        feedback_pool=2,
        feedback_count=2,
        iterations=2,
        seed=7,
    )

    assert report["protocol"]["queries"] == 3
    assert len(report["sampled_query_ids"]) == 3
    assert report["baseline"]["precision_at_k"] == 1.0
    assert report["fre_iterations"][0]["feedback_applied"] == 3
    assert report["fre_iterations"][1]["feedback_applied"] == 3
    assert report["fre_iterations"][1]["recall_at_k"] == 0.5


def test_evaluate_fre_skips_queries_without_two_positive_examples(tmp_path: Path) -> None:
    dataset = _make_dataset(
        tmp_path,
        {
            "red": [(255, 0, 0)],
            "green": [(0, 255, 0)],
            "blue": [(0, 0, 255)],
        },
    )
    index = build_index(dataset, tmp_path / "features.npz")

    report = evaluate_fre(
        index,
        query_count=3,
        top_k=1,
        feedback_pool=2,
        feedback_count=2,
        iterations=1,
    )

    iteration = report["fre_iterations"][0]
    assert iteration["feedback_applied"] == 0
    assert iteration["feedback_skipped"] == 3
    assert iteration["precision_at_k"] == report["baseline"]["precision_at_k"] == 0.0
