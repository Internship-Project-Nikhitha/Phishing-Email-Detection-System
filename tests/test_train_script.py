"""Tests for scripts/train.py (skipped if scikit-learn/joblib are not installed)."""

import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("joblib")

from scripts import train  # noqa: E402
from src import bundle, splitting  # noqa: E402
from src import data_prep  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT_ROOT / "tests" / "fixtures" / "sample_dataset.json"
FAST_MODELS = ["tfidf_logreg", "tfidf_naive_bayes"]


def test_run_training_selects_a_model_and_reports_validation_metrics():
    report, best = train.run_training(CONFIG, base_dir=PROJECT_ROOT, model_names=FAST_MODELS)

    assert [m["name"] for m in report["models"]] == FAST_MODELS
    assert report["selected_model"] in FAST_MODELS
    assert best.version.startswith(report["selected_model"])
    for item in report["models"]:
        assert 0.0 <= item["validation_metrics"]["f1"] <= 1.0


def test_metadata_proves_the_test_split_was_not_used_for_training():
    _, best = train.run_training(CONFIG, base_dir=PROJECT_ROOT, model_names=FAST_MODELS)
    prepared = data_prep.prepare_splits(CONFIG, base_dir=PROJECT_ROOT, random_state=42, duplicate_level="near")

    assert best.metadata["split_fingerprint"] == splitting.fingerprint_split(prepared.splits, "near")
    assert "test split untouched" in best.metadata["evaluated_on"]


def test_unknown_model_names_are_rejected():
    with pytest.raises(ValueError, match="Unknown model names"):
        train.run_training(CONFIG, base_dir=PROJECT_ROOT, model_names=["magic_forest"])


def test_main_writes_reports_and_a_loadable_model(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.setattr(train.models, "available_models", _only_fast(train.models.available_models))

    code = train.main(["--config", str(CONFIG), "--out-dir", str(tmp_path / "r"), "--model-dir", str(tmp_path / "m")])

    assert code == 0
    data = json.loads((tmp_path / "r" / "model_comparison.json").read_text(encoding="utf-8"))
    assert data["selected_model"] in FAST_MODELS
    text = (tmp_path / "r" / "model_comparison.md").read_text(encoding="utf-8")
    assert "test split was not used" in text
    assert bundle.load_bundle(tmp_path / "m").version == data["selected_version"]


def _only_fast(original):
    def limited():
        return {name: spec for name, spec in original().items() if name in FAST_MODELS}

    return limited


def test_main_returns_error_code_for_a_bad_config(tmp_path, capsys):
    code = train.main(["--config", str(tmp_path / "x.json"), "--out-dir", str(tmp_path), "--model-dir", str(tmp_path / "m")])

    assert code == 1
    assert "Error:" in capsys.readouterr().err
