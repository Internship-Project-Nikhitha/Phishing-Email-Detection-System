"""The saved model's metadata must agree with the model comparison and the final evaluation."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def meta():
    return load("models/latest/model_meta.json")


@pytest.fixture(scope="module")
def comparison():
    return load("reports/model_comparison.json")


@pytest.fixture(scope="module")
def final():
    return load("reports/final_evaluation.json")


def test_selected_model_is_the_one_that_was_evaluated(meta, comparison, final):
    assert meta["model_name"] == comparison["selected_model"] == final["model_name"]
    assert meta["version"] == comparison["selected_version"] == final["model_version"]


def test_seed_threshold_and_split_sizes_agree(meta, comparison, final):
    assert meta["seed"] == comparison["seed"] == final["seed"]
    assert meta["threshold"] == comparison["threshold"] == final["threshold"]
    assert meta["split_sizes"] == comparison["split_sizes"]


def test_ratios_sum_to_one_and_sizes_are_positive(meta):
    assert sum(meta["ratios"]) == pytest.approx(1.0)
    assert all(size > 0 for size in meta["split_sizes"].values())


def test_validation_metrics_match_the_comparison_table(meta, comparison):
    chosen = next(m for m in comparison["models"] if m["name"] == meta["model_name"])
    assert chosen["validation_metrics"] == meta["validation_metrics"]


def test_selection_rule_was_followed(comparison):
    """Highest validation F1; a tie is broken by the lower false-positive rate."""
    def key(model):
        metrics = model["validation_metrics"]
        return (-metrics["f1"], metrics["false_positive_rate"])

    best = min(comparison["models"], key=key)
    assert best["name"] == comparison["selected_model"]


def test_metadata_says_the_test_split_was_not_used_for_training(meta):
    assert "test split untouched" in meta["evaluated_on"]


def test_feature_counts_are_consistent(meta):
    assert 0 < meta["engineered_feature_count"] <= meta["total_feature_count"]
