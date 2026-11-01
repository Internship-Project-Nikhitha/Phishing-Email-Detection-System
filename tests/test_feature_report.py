"""Tests for scripts/feature_report.py."""

from pathlib import Path

import pytest

from scripts import feature_report
from src import data_prep
from src.features import pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT_ROOT / "tests" / "fixtures" / "sample_dataset.json"


def test_class_means_on_a_tiny_example():
    records = [
        {"subject": "A", "body": "http://a.example.invalid", "sender": "", "label": "phishing"},
        {"subject": "B", "body": "http://a.example.invalid http://b.example.invalid", "sender": "", "label": "phishing"},
        {"subject": "C", "body": "no links", "sender": "", "label": "legitimate"},
    ]

    means = feature_report.class_means(records)

    assert means["url_count"] == {"phishing": pytest.approx(1.5), "legitimate": 0.0}
    assert list(means) == pipeline.feature_names()


def test_class_means_handles_a_missing_class():
    means = feature_report.class_means([{"subject": "A", "body": "x", "sender": "", "label": "phishing"}])

    assert all(value["legitimate"] == 0.0 for value in means.values())


def test_markdown_lists_every_feature_with_its_meaning():
    train = data_prep.prepare_splits(CONFIG, base_dir=PROJECT_ROOT, duplicate_level="near").splits.train

    text = feature_report.to_markdown(feature_report.class_means(train), len(train))

    for name in pipeline.feature_names():
        assert f"| {name} |" in text
    assert f"from {len(train)} training emails" in text


def test_main_writes_the_report(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    out = tmp_path / "stats.md"

    assert feature_report.main(["--config", str(CONFIG), "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("# Feature statistics")


def test_main_reports_errors(tmp_path, capsys):
    assert feature_report.main(["--config", str(tmp_path / "x.json"), "--out", str(tmp_path / "o.md")]) == 1
    assert "Error:" in capsys.readouterr().err
