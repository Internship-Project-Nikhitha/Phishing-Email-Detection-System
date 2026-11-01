"""Tests for scripts/run_baseline.py (skipped if scikit-learn is not installed)."""

import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from scripts import run_baseline  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT_ROOT / "tests" / "fixtures" / "sample_dataset.json"


def test_run_baseline_reports_real_counts_and_uses_validation_only():
    report = run_baseline.run_baseline(CONFIG, seed=42, base_dir=PROJECT_ROOT)

    assert report["evaluated_on"] == "validation"
    assert report["rows_read"] == 58
    assert sum(report["split_sizes"].values()) == 48
    metrics = report["validation_metrics"]
    assert metrics["tp"] + metrics["fp"] + metrics["tn"] + metrics["fn"] == report["split_sizes"]["validation"]
    assert 0.0 <= metrics["f1"] <= 1.0


def test_run_baseline_is_reproducible():
    first = run_baseline.run_baseline(CONFIG, seed=3, base_dir=PROJECT_ROOT)["validation_metrics"]
    second = run_baseline.run_baseline(CONFIG, seed=3, base_dir=PROJECT_ROOT)["validation_metrics"]

    assert first == second


def test_markdown_states_that_the_test_split_was_not_used():
    report = run_baseline.run_baseline(CONFIG, base_dir=PROJECT_ROOT)

    text = run_baseline.to_markdown(report)

    assert "the test split was not used" in text
    assert "| F1-score |" in text


def test_main_writes_json_and_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)

    code = run_baseline.main(["--config", str(CONFIG), "--out-dir", str(tmp_path)])

    assert code == 0
    data = json.loads((tmp_path / "baseline_metrics.json").read_text(encoding="utf-8"))
    assert data["model"].startswith("TF-IDF")
    assert (tmp_path / "baseline_metrics.md").exists()


def test_main_returns_error_code_for_a_bad_config(tmp_path, capsys):
    code = run_baseline.main(["--config", str(tmp_path / "x.json"), "--out-dir", str(tmp_path)])

    assert code == 1
    assert "Error:" in capsys.readouterr().err
