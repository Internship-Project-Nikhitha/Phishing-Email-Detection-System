"""Tests for the loader's error-reason summary (src/dataset.py)."""

from pathlib import Path

import pytest

from src import dataset as ds
from src.preprocessing import RecordError

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.parametrize(
    "message, expected",
    [
        ("Unknown label 'spam'. Supported ...", "unknown label"),
        ("Label is missing.", "missing or empty label"),
        ("Label is empty.", "missing or empty label"),
        ("Email has no usable content: 'subject' and 'body' are both missing or empty.", "no usable content"),
        ("Field 'body' must be a string, got list.", "wrong field type"),
        ("Something else", "other"),
    ],
)
def test_categorize_error(message, expected):
    assert ds.categorize_error(message) == expected


def test_count_error_reasons_on_the_fixture_dataset():
    config = ds.load_config(FIXTURES / "sample_dataset.json")

    result = ds.load_dataset(config, base_dir=FIXTURES.parent.parent)

    counts = ds.count_error_reasons(result.errors)
    assert sum(counts.values()) == len(result.errors)
    assert len(result.errors) > 0
    assert set(counts) <= {"unknown label", "missing or empty label", "no usable content", "wrong field type", "other"}


def test_count_error_reasons_with_no_errors_is_empty():
    assert ds.count_error_reasons([]) == {}


def test_count_error_reasons_groups_and_sorts():
    errors = [RecordError(index=0, message="Label is missing."), RecordError(index=1, message="Unknown label 'x'."),
              RecordError(index=2, message="Label is empty.")]

    assert ds.count_error_reasons(errors) == {"missing or empty label": 2, "unknown label": 1}
