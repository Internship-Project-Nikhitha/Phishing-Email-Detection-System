"""Tests for scripts/evaluate.py (skipped if scikit-learn/joblib are not installed)."""

import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("joblib")

from scripts import evaluate, train  # noqa: E402
from src import bundle  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT_ROOT / "tests" / "fixtures" / "sample_dataset.json"


@pytest.fixture(scope="module")
def model_dir(tmp_path_factory):
    folder = tmp_path_factory.mktemp("model")
    _, best = train.run_training(CONFIG, base_dir=PROJECT_ROOT, model_names=["tfidf_logreg"])
    bundle.save_bundle(best, folder)
    return folder


def test_calibration_table_bins_scores():
    table = evaluate.calibration_table([0.05, 0.1, 0.95, 1.0, 0.5], ["legitimate", "legitimate", "phishing", "phishing", "phishing"])

    assert [row["emails"] for row in table] == [2, 0, 1, 0, 2]
    assert table[0]["observed_phishing_rate"] == 0.0
    assert table[1]["observed_phishing_rate"] is None
    assert table[4]["observed_phishing_rate"] == 1.0


def test_calibration_table_validates_input():
    with pytest.raises(ValueError):
        evaluate.calibration_table([], [])
    with pytest.raises(ValueError):
        evaluate.calibration_table([0.5], ["phishing", "legitimate"])


def test_run_evaluation_uses_the_test_split_and_reports_real_counts(model_dir):
    report = evaluate.run_evaluation(CONFIG, model_dir, base_dir=PROJECT_ROOT)

    m = report["test_metrics"]
    assert m["tp"] + m["fp"] + m["tn"] + m["fn"] == report["test_size"]
    assert len(report["false_positive_ids"]) == m["fp"]
    assert len(report["false_negative_ids"]) == m["fn"]
    assert sum(row["emails"] for row in report["calibration"]) == report["test_size"]
    assert report["latency_single_message"]["median_ms"] >= 0


def test_evaluation_refuses_a_test_split_that_does_not_match_training(model_dir, tmp_path):
    copy = tmp_path / "model"
    bundle.save_bundle(bundle.load_bundle(model_dir), copy)
    meta_path = copy / "model_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["split_fingerprint"] = "0" * 64
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(RuntimeError, match="does not match"):
        evaluate.run_evaluation(CONFIG, copy, base_dir=PROJECT_ROOT)


def test_report_contains_no_email_text_and_main_writes_files(model_dir, tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)

    code = evaluate.main(["--config", str(CONFIG), "--model-dir", str(model_dir), "--out-dir", str(tmp_path)])

    assert code == 0
    text = (tmp_path / "final_evaluation.md").read_text(encoding="utf-8")
    assert "# Final evaluation (held-out test split)" in text
    assert "password" not in text and "example.invalid" not in text
    assert json.loads((tmp_path / "final_evaluation.json").read_text(encoding="utf-8"))["test_size"] > 0


def test_main_reports_a_missing_model(tmp_path, capsys):
    code = evaluate.main(["--config", str(CONFIG), "--model-dir", str(tmp_path / "none"), "--out-dir", str(tmp_path)])

    assert code == 1
    assert "python scripts/train.py" in capsys.readouterr().err
