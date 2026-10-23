"""Tests for src/data_prep.py."""

import csv

from src.data_prep import prepare_splits
from src.dataset import DatasetConfig
from src.splitting import SPLIT_NAMES, assert_no_duplicate_leakage


def make_csv(tmp_path, *, include_invalid=False, include_duplicate=False):
    """Create a deterministic, balanced CSV dataset for pipeline tests."""
    path = tmp_path / "emails.csv"

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Subject", "Body", "Sender", "Label"])

        for label in ("phishing", "legitimate"):
            for number in range(40):
                writer.writerow([
                    f"{label} subject alpha{number}",
                    f"{label} body beta{number} unique",
                    f"user{number}@example.com",
                    label,
                ])

        if include_duplicate:
            writer.writerow([
                "phishing subject alpha0",
                "phishing body beta0 unique",
                "user0@example.com",
                "phishing",
            ])

        if include_invalid:
            writer.writerow(["", "", "broken@example.com", "phishing"])

    return path


def make_config(csv_path):
    return DatasetConfig(
        path=str(csv_path),
        columns={
            "subject": "Subject",
            "body": "Body",
            "sender": "Sender",
            "label": "Label",
        },
    )


def test_prepare_splits_loads_and_splits_valid_records(tmp_path):
    csv_path = make_csv(tmp_path)
    result = prepare_splits(make_config(csv_path))

    assert result.valid_count == 80
    assert result.invalid_count == 0
    assert result.errors == []
    assert sum(result.sizes().values()) == 80
    assert all(result.sizes()[name] > 0 for name in SPLIT_NAMES)


def test_prepare_splits_preserves_invalid_record_errors(tmp_path):
    csv_path = make_csv(tmp_path, include_invalid=True)
    result = prepare_splits(make_config(csv_path))

    assert result.valid_count == 80
    assert result.invalid_count == 1
    assert result.errors[0].index == 80
    assert sum(result.sizes().values()) == 80


def test_prepare_splits_reports_duplicate_groups(tmp_path):
    csv_path = make_csv(tmp_path, include_duplicate=True)
    result = prepare_splits(make_config(csv_path))

    assert result.valid_count == 81
    assert result.duplicate_groups
    assert any(len(indexes) == 2 for indexes in result.duplicate_groups.values())

    assert_no_duplicate_leakage(result.splits, duplicate_level="exact")


def test_prepare_splits_is_reproducible(tmp_path):
    csv_path = make_csv(tmp_path)
    config = make_config(csv_path)

    first = prepare_splits(config, random_state=17)
    second = prepare_splits(config, random_state=17)

    assert first.records == second.records
    assert first.duplicate_groups == second.duplicate_groups
    assert first.splits == second.splits
