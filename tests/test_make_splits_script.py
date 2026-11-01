"""Tests for scripts/make_splits.py."""

import csv
from pathlib import Path

from scripts import make_splits
from src import data_prep

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT_ROOT / "tests" / "fixtures" / "sample_dataset.json"


def test_build_summary_lists_all_splits_and_the_check():
    prepared = data_prep.prepare_splits(CONFIG, base_dir=PROJECT_ROOT, duplicate_level="near")

    text = make_splits.build_summary(prepared)

    assert "Seed: **42**" in text
    assert "Records after duplicate removal: **48**" in text
    assert "Leakage check: **passed**" in text
    for name in ("train", "validation", "test"):
        assert f"| {name} |" in text


def test_main_writes_split_ids_and_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)

    code = make_splits.main(["--config", str(CONFIG), "--out-dir", str(tmp_path)])

    assert code == 0
    with (tmp_path / "split_ids.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert len(rows) - 1 == 48
    assert (tmp_path / "split_summary.md").read_text(encoding="utf-8").startswith("# Train/validation/test split")


def test_main_returns_error_code_for_a_bad_config(tmp_path, capsys):
    code = make_splits.main(["--config", str(tmp_path / "nope.json"), "--out-dir", str(tmp_path)])

    assert code == 1
    assert "Error:" in capsys.readouterr().err
