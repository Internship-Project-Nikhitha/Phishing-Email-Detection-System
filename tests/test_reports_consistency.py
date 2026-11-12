"""The committed final evaluation must be internally consistent and match the other reports.

These tests read the committed files in ``reports/``. They never recompute a model.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


@pytest.fixture(scope="module")
def final():
    return json.loads((REPORTS / "final_evaluation.json").read_text(encoding="utf-8"))


def test_confusion_counts_add_up(final):
    m = final["test_metrics"]
    assert m["tp"] + m["fp"] + m["tn"] + m["fn"] == final["test_size"]
    assert m["support_positive"] == m["tp"] + m["fn"]
    assert m["support_negative"] == m["tn"] + m["fp"]


def test_metrics_match_the_confusion_counts(final):
    m = final["test_metrics"]
    tp, fp, tn, fn = m["tp"], m["fp"], m["tn"], m["fn"]
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    assert m["accuracy"] == pytest.approx((tp + tn) / (tp + fp + tn + fn), abs=1e-9)
    assert m["precision"] == pytest.approx(precision, abs=1e-9)
    assert m["recall"] == pytest.approx(recall, abs=1e-9)
    assert m["f1"] == pytest.approx(2 * precision * recall / (precision + recall), abs=1e-9)
    assert m["false_positive_rate"] == pytest.approx(fp / (fp + tn), abs=1e-9)
    assert m["false_negative_rate"] == pytest.approx(fn / (fn + tp), abs=1e-9)


def test_error_id_lists_match_the_counts(final):
    m = final["test_metrics"]
    false_positives, false_negatives = final["false_positive_ids"], final["false_negative_ids"]
    assert len(false_positives) == m["fp"]
    assert len(false_negatives) == m["fn"]
    assert len(set(false_positives)) == len(false_positives)
    assert len(set(false_negatives)) == len(false_negatives)
    assert not set(false_positives) & set(false_negatives)


def test_calibration_table_covers_every_test_email(final):
    m = final["test_metrics"]
    bins = final["calibration"]
    assert sum(b["emails"] for b in bins) == final["test_size"]
    assert sum(b["phishing"] for b in bins) == m["support_positive"]
    for b in bins:
        if b["emails"]:
            assert b["observed_phishing_rate"] == pytest.approx(b["phishing"] / b["emails"], abs=1e-3)


def test_same_split_fingerprint_everywhere(final):
    fingerprint = final["split_fingerprint"]
    assert len(fingerprint) == 64
    assert fingerprint in (REPORTS / "split_summary.md").read_text(encoding="utf-8")
    assert fingerprint in (REPORTS / "final_evaluation.md").read_text(encoding="utf-8")
    meta = json.loads((ROOT / "models" / "latest" / "model_meta.json").read_text(encoding="utf-8"))
    assert meta["split_fingerprint"] == fingerprint


def test_test_size_matches_the_training_report(final):
    comparison = json.loads((REPORTS / "model_comparison.json").read_text(encoding="utf-8"))
    assert final["test_size"] == comparison["split_sizes"]["test"]
