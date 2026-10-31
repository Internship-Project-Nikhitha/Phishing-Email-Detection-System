"""Classification metrics for phishing detection (Member 5).

Phishing is the "positive" class. Definitions:

* precision = TP / (TP + FP)      of the emails flagged as phishing, how many really were
* recall    = TP / (TP + FN)      of the real phishing emails, how many were caught
* F1        = 2 * precision * recall / (precision + recall)
* false-positive rate = FP / (FP + TN)   legitimate emails wrongly flagged
* false-negative rate = FN / (FN + TP)   phishing emails missed

Any ratio whose denominator is 0 is reported as 0.0 (and the counts show why).
"""

from typing import Any

LABELS = ("phishing", "legitimate")


def _check_inputs(y_true: list[str], y_pred: list[str], positive: str) -> None:
    if len(y_true) != len(y_pred):
        raise ValueError(f"y_true and y_pred must have the same length ({len(y_true)} vs {len(y_pred)}).")
    if len(y_true) == 0:
        raise ValueError("Cannot compute metrics on empty lists.")
    if positive not in LABELS:
        raise ValueError(f"positive must be one of {LABELS}, got {positive!r}.")
    for name, values in (("y_true", y_true), ("y_pred", y_pred)):
        unknown = sorted({value for value in values if value not in LABELS}, key=str)
        if unknown:
            raise ValueError(f"{name} contains unknown labels: {unknown}. Expected only {LABELS}.")


def confusion_counts(y_true: list[str], y_pred: list[str], positive: str = "phishing") -> dict[str, int]:
    """Count true/false positives and negatives.

    Args:
        y_true: Real labels (``'phishing'`` or ``'legitimate'``).
        y_pred: Predicted labels, same length as ``y_true``.
        positive: The label treated as the positive class.

    Returns:
        ``{"tp": ..., "fp": ..., "tn": ..., "fn": ...}``.

    Raises:
        ValueError: On different lengths, empty input or unknown labels.
    """
    _check_inputs(y_true, y_pred, positive)
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for actual, predicted in zip(y_true, y_pred):
        if predicted == positive:
            counts["tp" if actual == positive else "fp"] += 1
        else:
            counts["fn" if actual == positive else "tn"] += 1
    return counts


def safe_divide(numerator: float, denominator: float) -> float:
    """Return ``numerator / denominator``, or 0.0 when the denominator is 0."""
    return numerator / denominator if denominator else 0.0


def compute_metrics(y_true: list[str], y_pred: list[str], positive: str = "phishing") -> dict[str, Any]:
    """Compute accuracy, precision, recall, F1, false-positive and false-negative rates.

    Returns:
        A dict with the confusion counts (``tp``, ``fp``, ``tn``, ``fn``), the
        class sizes (``support_positive``, ``support_negative``) and the float
        metrics ``accuracy``, ``precision``, ``recall``, ``f1``,
        ``false_positive_rate`` and ``false_negative_rate``.
    """
    counts = confusion_counts(y_true, y_pred, positive)
    tp, fp, tn, fn = counts["tp"], counts["fp"], counts["tn"], counts["fn"]
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    return {
        **counts,
        "support_positive": tp + fn,
        "support_negative": tn + fp,
        "accuracy": safe_divide(tp + tn, tp + fp + tn + fn),
        "precision": precision,
        "recall": recall,
        "f1": safe_divide(2 * precision * recall, precision + recall),
        "false_positive_rate": safe_divide(fp, fp + tn),
        "false_negative_rate": safe_divide(fn, fn + tp),
    }


def format_metrics_markdown(metrics: dict[str, Any], title: str = "Metrics") -> str:
    """Render ``compute_metrics`` output as a Markdown section with a confusion matrix."""
    lines = [
        f"## {title}",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Accuracy | {metrics['accuracy']:.4f} |",
        f"| Precision | {metrics['precision']:.4f} |",
        f"| Recall | {metrics['recall']:.4f} |",
        f"| F1-score | {metrics['f1']:.4f} |",
        f"| False-positive rate | {metrics['false_positive_rate']:.4f} |",
        f"| False-negative rate | {metrics['false_negative_rate']:.4f} |",
        "",
        "Confusion matrix (phishing = positive class):",
        "",
        "| | Predicted phishing | Predicted legitimate |",
        "|---|---|---|",
        f"| **Actual phishing** | {metrics['tp']} (TP) | {metrics['fn']} (FN) |",
        f"| **Actual legitimate** | {metrics['fp']} (FP) | {metrics['tn']} (TN) |",
        "",
    ]
    return "\n".join(lines)
