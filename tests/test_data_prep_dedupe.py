"""Tests that the data pipeline removes duplicates and label conflicts before splitting."""

import csv

import pytest

from src.data_prep import prepare_splits
from src.dataset import DatasetConfig
from src.splitting import SPLIT_NAMES, assert_no_duplicate_leakage

COLUMNS = {"subject": "Subject", "body": "Body", "sender": "Sender", "label": "Label"}


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Subject", "Body", "Sender", "Label"])
        writer.writerows(rows)


def word(number):
    """A letters-only token, because near-duplicate keys ignore digits."""
    return "".join(chr(97 + int(digit)) for digit in str(number))


def base_rows():
    rows = []
    for label in ("phishing", "legitimate"):
        for number in range(30):
            rows.append([f"{label} subject alpha{word(number)}", f"{label} body beta{word(number)} unique",
                         f"user{number}@example.com", label])
    return rows


def run(tmp_path, extra_rows, level="exact"):
    path = tmp_path / "emails.csv"
    write_rows(path, base_rows() + extra_rows)
    config = DatasetConfig(path=str(path), columns=COLUMNS)
    return prepare_splits(config, duplicate_level=level)


def test_conflicting_label_duplicates_are_removed_instead_of_crashing(tmp_path):
    conflict = [
        ["same text", "same body", "a@example.com", "phishing"],
        ["same text", "same body", "b@example.com", "legitimate"],
    ]

    result = run(tmp_path, conflict)

    reasons = [item.reason for item in result.dedup.removed]
    assert sum(reason.startswith("conflicting_labels") for reason in reasons) == 2
    assert sum(result.sizes().values()) == 60
    assert all(record["subject"] != "same text" for name in SPLIT_NAMES for record in result.splits.by_name(name))


def test_exact_duplicates_keep_only_the_first_copy(tmp_path):
    copies = [["phishing subject alphaa", "phishing body betaa unique", "x@example.com", "phishing"]] * 3

    result = run(tmp_path, copies)

    assert len(result.dedup.removed) == 3
    assert sum(result.sizes().values()) == 60


@pytest.mark.parametrize("level", ["exact", "near"])
def test_no_leakage_after_deduplication(tmp_path, level):
    extra = [["phishing subject alphab", "phishing body betab unique", "y@example.com", "phishing"],
             ["conflict", "conflict body", "a@example.com", "phishing"],
             ["conflict", "conflict body", "b@example.com", "legitimate"]]

    result = run(tmp_path, extra, level=level)

    assert_no_duplicate_leakage(result.splits, duplicate_level=level)
    assert result.valid_count == 63
