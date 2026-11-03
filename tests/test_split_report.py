"""Tests for src/split_report.py (counts and IDs only, never email text)."""

import csv
from pathlib import Path

from src import data_prep, dataset, quality, split_report
from src.keys import record_id

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT_ROOT / "tests" / "fixtures" / "sample_dataset.json"


def _prepared():
    return data_prep.prepare_splits(CONFIG, base_dir=PROJECT_ROOT, duplicate_level="near")


def test_summarize_split_counts_every_split_and_label():
    prepared = _prepared()

    summary = split_report.summarize_split(prepared.splits)

    assert set(summary) == {"train", "validation", "test"}
    assert sum(item["size"] for item in summary.values()) == 48
    for name, item in summary.items():
        assert sum(item["labels"].values()) == item["size"] == len(prepared.splits.by_name(name))


def test_write_split_ids_has_ids_and_labels_but_no_email_text(tmp_path):
    prepared = _prepared()

    rows = split_report.write_split_ids(prepared.splits, tmp_path / "ids" / "split_ids.csv")

    text = (tmp_path / "ids" / "split_ids.csv").read_text(encoding="utf-8")
    assert rows == 48
    assert text.splitlines()[0] == "split,id,label"
    first = prepared.splits.train[0]
    assert record_id(first) in text
    assert first["body"] not in text and first["subject"] not in text
    with (tmp_path / "ids" / "split_ids.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.reader(handle))) == 49


def test_format_quality_markdown_has_counts_and_label_table():
    loaded = dataset.load_dataset(CONFIG, base_dir=PROJECT_ROOT)
    audit = quality.audit_quality(loaded.valid, level="near")

    text = split_report.format_quality_markdown(audit, "Quality", loaded.valid)

    assert text.startswith("## Quality")
    assert f"| Valid records | {audit.valid_records} |" in text
    assert "| phishing | 29 | 52.73% |" in text


def test_count_removed_splits_reasons():
    loaded = dataset.load_dataset(CONFIG, base_dir=PROJECT_ROOT)
    dedup = quality.deduplicate(loaded.valid, level="near")

    counts = split_report.count_removed(dedup)

    assert counts == {"duplicates": 5, "conflicts": 2, "malformed": 0}
