"""Tests for src/baseline.py (skipped automatically if scikit-learn is not installed)."""

import pytest

pytest.importorskip("sklearn")

from src import baseline  # noqa: E402


def rec(subject, body, label):
    return {"subject": subject, "body": body, "sender": "", "label": label}


def tiny_training_set():
    phishing = [
        rec("Verify your password now", "Your account is locked, confirm your password at the link", "phishing"),
        rec("Urgent payment failed", "Update your card details immediately or lose access", "phishing"),
        rec("Account suspended", "Click the link to verify your account password today", "phishing"),
        rec("Prize winner", "Claim your prize by entering your bank details", "phishing"),
    ]
    legitimate = [
        rec("Meeting notes", "Attached are the notes from the planning meeting", "legitimate"),
        rec("Lunch on Friday", "Shall we meet at noon in the cafe near the office", "legitimate"),
        rec("Project schedule", "The schedule for the next sprint is in the shared calendar", "legitimate"),
        rec("Team newsletter", "This month's newsletter covers the new office layout", "legitimate"),
    ]
    return phishing + legitimate


def test_record_text_joins_subject_and_body_and_tolerates_missing_keys():
    assert baseline.record_text({"subject": "Hi", "body": "There"}) == "Hi\nThere"
    assert baseline.record_text({}) == "\n"


def test_train_baseline_learns_the_training_set():
    records = tiny_training_set()

    model = baseline.train_baseline(records)
    predictions = baseline.predict_labels(model, records)

    assert predictions == [r["label"] for r in records]


def test_predict_scores_are_probabilities_and_rank_phishing_higher():
    records = tiny_training_set()
    model = baseline.train_baseline(records)

    scores = baseline.predict_scores(model, records)

    assert all(0.0 <= score <= 1.0 for score in scores)
    phishing_scores = [s for s, r in zip(scores, records) if r["label"] == "phishing"]
    legitimate_scores = [s for s, r in zip(scores, records) if r["label"] == "legitimate"]
    assert min(phishing_scores) > max(legitimate_scores)


def test_baseline_generalizes_to_an_unseen_obvious_example():
    model = baseline.train_baseline(tiny_training_set())

    labels = baseline.predict_labels(
        model,
        [
            rec("Confirm your password", "Verify your account password at the link now", "phishing"),
            rec("Planning meeting", "Notes from the meeting are attached", "legitimate"),
        ],
    )

    assert labels == ["phishing", "legitimate"]


def test_training_is_reproducible():
    records = tiny_training_set()

    first = baseline.predict_scores(baseline.train_baseline(records, seed=1), records)
    second = baseline.predict_scores(baseline.train_baseline(records, seed=1), records)

    assert first == second


def test_train_baseline_rejects_empty_and_single_label_data():
    with pytest.raises(ValueError, match="empty"):
        baseline.train_baseline([])
    with pytest.raises(ValueError, match="both"):
        baseline.train_baseline([rec("a", "b", "phishing")])
