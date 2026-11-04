"""Tests for src/bundle.py (skipped if scikit-learn/joblib are not installed)."""

from datetime import datetime, timezone

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("joblib")

from src import bundle as bd  # noqa: E402
from src import models  # noqa: E402


def data():
    phishing = [
        {"subject": f"Verify password {w}", "body": f"Confirm your password at http://{w}.example.invalid", "sender": "", "label": "phishing"}
        for w in ("a", "b", "c", "d")
    ]
    legit = [
        {"subject": f"Meeting {w}", "body": f"Notes for the {w} meeting attached", "sender": "", "label": "legitimate"}
        for w in ("e", "f", "g", "h")
    ]
    return phishing + legit


def make_bundle():
    records = data()
    model = models.train_model(models.available_models()["tfidf_logreg"], records)
    return bd.ModelBundle(model=model, version="v-test", metadata={"seed": 1}), records


def test_make_version_is_stable_for_a_given_time():
    moment = datetime(2026, 11, 5, 10, 15, tzinfo=timezone.utc)

    assert bd.make_version("tfidf_logreg", moment) == "tfidf_logreg-20261105T101500Z"


def test_bundle_scores_and_explains_one_record():
    bundle, records = make_bundle()

    score = bundle.predict_score(records[0])
    explanation = bundle.contributions(records[0])

    assert 0.0 <= score <= 1.0
    assert explanation


def test_save_and_load_round_trip_gives_identical_scores(tmp_path):
    bundle, records = make_bundle()

    bd.save_bundle(bundle, tmp_path / "latest")
    loaded = bd.load_bundle(tmp_path / "latest")

    assert loaded.version == "v-test"
    assert loaded.metadata["seed"] == 1
    assert loaded.metadata["model_name"] == "tfidf_logreg"
    assert [loaded.predict_score(r) for r in records] == [bundle.predict_score(r) for r in records]


def test_load_bundle_reports_missing_files_with_a_hint(tmp_path):
    with pytest.raises(FileNotFoundError, match="python scripts/train.py"):
        bd.load_bundle(tmp_path / "nothing-here")
