"""Tests for src/metrics.py."""

import pytest

from src import metrics as m

P, L = "phishing", "legitimate"


def test_confusion_counts_on_a_known_example():
    y_true = [P, P, P, L, L, L, L]
    y_pred = [P, P, L, L, L, P, L]

    assert m.confusion_counts(y_true, y_pred) == {"tp": 2, "fp": 1, "tn": 3, "fn": 1}


def test_confusion_counts_with_legitimate_as_positive_swaps_roles():
    y_true = [P, P, L]
    y_pred = [P, L, L]

    assert m.confusion_counts(y_true, y_pred, positive=L) == {"tp": 1, "fp": 1, "tn": 1, "fn": 0}


@pytest.mark.parametrize(
    "y_true, y_pred, positive, message",
    [
        ([P], [P, L], P, "same length"),
        ([], [], P, "empty"),
        ([P], [P], "spam", "positive must be"),
        ([P, "spam"], [P, L], P, "y_true contains unknown labels"),
        ([P, L], [P, "maybe"], P, "y_pred contains unknown labels"),
    ],
)
def test_confusion_counts_rejects_bad_input(y_true, y_pred, positive, message):
    with pytest.raises(ValueError, match=message):
        m.confusion_counts(y_true, y_pred, positive)


def test_safe_divide():
    assert m.safe_divide(1, 4) == 0.25
    assert m.safe_divide(5, 0) == 0.0


def test_compute_metrics_matches_hand_calculation():
    # tp=2, fp=1, tn=3, fn=1  ->  precision 2/3, recall 2/3, accuracy 5/7
    y_true = [P, P, P, L, L, L, L]
    y_pred = [P, P, L, L, L, P, L]

    result = m.compute_metrics(y_true, y_pred)

    assert (result["tp"], result["fp"], result["tn"], result["fn"]) == (2, 1, 3, 1)
    assert result["precision"] == pytest.approx(2 / 3)
    assert result["recall"] == pytest.approx(2 / 3)
    assert result["f1"] == pytest.approx(2 / 3)
    assert result["accuracy"] == pytest.approx(5 / 7)
    assert result["false_positive_rate"] == pytest.approx(1 / 4)
    assert result["false_negative_rate"] == pytest.approx(1 / 3)
    assert result["support_positive"] == 3
    assert result["support_negative"] == 4


def test_perfect_predictions():
    y = [P, L, P, L]

    result = m.compute_metrics(y, y)

    assert result["precision"] == result["recall"] == result["f1"] == result["accuracy"] == 1.0
    assert result["false_positive_rate"] == result["false_negative_rate"] == 0.0


def test_no_predicted_positives_gives_zero_precision_not_a_crash():
    result = m.compute_metrics([P, L], [L, L])

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0
    assert result["false_positive_rate"] == 0.0


def test_only_one_class_present_does_not_divide_by_zero():
    result = m.compute_metrics([L, L], [L, P])

    assert result["false_positive_rate"] == 0.5
    assert result["recall"] == 0.0
    assert result["support_positive"] == 0


def test_format_metrics_markdown_contains_values_and_matrix():
    result = m.compute_metrics([P, P, L, L], [P, L, L, P])

    text = m.format_metrics_markdown(result, title="Validation metrics")

    assert text.startswith("## Validation metrics")
    assert "| Precision | 0.5000 |" in text
    assert "| False-positive rate | 0.5000 |" in text
    assert "| **Actual phishing** | 1 (TP) | 1 (FN) |" in text
    assert "| **Actual legitimate** | 1 (FP) | 1 (TN) |" in text
