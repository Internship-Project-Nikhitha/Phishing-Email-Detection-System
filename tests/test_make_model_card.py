"""Tests for scripts/make_model_card.py."""

import json

from scripts import make_model_card

METRICS = {"precision": 0.9, "recall": 0.8, "f1": 0.8471, "false_positive_rate": 0.05, "false_negative_rate": 0.2}
META = {
    "model_name": "tfidf_logreg",
    "version": "tfidf_logreg-20261105T101500Z",
    "created_at": "2026-11-05T10:15:00+00:00",
    "mode": "text",
    "total_feature_count": 1234,
    "engineered_feature_count": 29,
    "params": {"C": 1.0},
    "threshold": 0.5,
    "dataset_config": "configs/dataset.json",
    "seed": 42,
    "dedup_level": "near",
    "ratios": [0.7, 0.15, 0.15],
    "split_sizes": {"train": 70, "validation": 15, "test": 15},
    "evaluated_on": "validation (test split untouched)",
    "validation_metrics": METRICS,
}
COMPARISON = {"models": [{"name": "tfidf_logreg", "validation_metrics": METRICS}]}


def test_model_card_copies_numbers_from_the_inputs():
    card = make_model_card.build_model_card(META, COMPARISON)

    assert "`tfidf_logreg-20261105T101500Z`" in card
    assert "| F1-score | 0.8471 |" in card
    assert "| tfidf_logreg | 0.8471 | 0.0500 |" in card
    assert "{'train': 70, 'validation': 15, 'test': 15}" in card
    assert "test split untouched" in card


def test_main_writes_the_card_from_json_files(tmp_path):
    (tmp_path / "meta.json").write_text(json.dumps(META), encoding="utf-8")
    (tmp_path / "cmp.json").write_text(json.dumps(COMPARISON), encoding="utf-8")
    out = tmp_path / "docs" / "model-card.md"

    code = make_model_card.main(
        ["--meta", str(tmp_path / "meta.json"), "--comparison", str(tmp_path / "cmp.json"), "--out", str(out)]
    )

    assert code == 0
    assert out.read_text(encoding="utf-8").startswith("# Model card")


def test_main_explains_missing_inputs(tmp_path, capsys):
    code = make_model_card.main(["--meta", str(tmp_path / "no.json"), "--comparison", str(tmp_path / "no2.json")])

    assert code == 1
    assert "python scripts/train.py" in capsys.readouterr().err
