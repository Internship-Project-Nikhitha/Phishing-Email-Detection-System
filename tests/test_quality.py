


"""Tests for dataset quality checks and deduplication."""

import pytest


from src.quality import (
    audit_quality,
    deduplicate,
    find_duplicate_groups,
)

def make(subject="Hello", body="World", label="Safe Email"):
    return {
        "subject": subject,
        "body": body,
        "sender": "",
        "label": label,
    }


def test_exact_duplicates_are_grouped():
    records = [
        make("Account Alert", "Verify your account"),
        make("Account Alert", "Verify your account"),
        make("Different", "Unique message"),
    ]

    groups = find_duplicate_groups(records, level="exact")

    assert len(groups) == 1
    assert list(groups.values()) == [[0, 1]]


def test_near_duplicates_are_grouped():
    records = [
        make("Dear user 123", "Visit http://first.example.invalid/login now!"),
        make("Dear user 456", "Visit http://second.example.invalid/login now."),
        make("Team lunch", "See you at noon"),
    ]

    groups = find_duplicate_groups(records, level="near")

    assert len(groups) == 1
    assert list(groups.values()) == [[0, 1]]


def test_deduplicate_is_deterministic():
    records = [
        make("Account Alert", "Verify your account"),
        make("Different", "Unique message"),
    ]

    first = deduplicate(records, level="exact")
    second = deduplicate(records, level="exact")

    assert first == second


def test_label_variants_are_normalized():
    records = [
        make("Account alert", "Verify account 123", "Phishing"),
        make("Account alert", "Verify account 123", "phishing"),
    ]

    result = deduplicate(records, level="exact")

    assert len(result.records) == 1
    assert len(result.removed) == 1
    assert result.removed[0].reason == (
        "duplicate: same content key and label"
    )


def test_conflicting_labels_exclude_entire_group():
    records = [
        make("Account alert", "Verify account 123", "Phishing Email"),
        make("Account alert", "Verify account 123", "Safe Email"),
    ]

    result = deduplicate(records, level="exact")

    assert result.records == []
    assert len(result.removed) == 2
    assert all(
        item.reason.startswith("conflicting_labels:")
        for item in result.removed
    )


def test_missing_label_is_removed():
    records = [make("Account alert", "Verify account 123", "")]

    result = deduplicate(records, level="exact")

    assert result.records == []
    assert len(result.removed) == 1
    assert result.removed[0].reason.startswith("malformed_record:")


def test_missing_subject_is_removed():
    records = [
        {
            "subject": None,
            "body": "Verify your account",
            "sender": "",
            "label": "Safe Email",
        }
    ]

    result = deduplicate(records, level="exact")

    assert result.records == []
    assert len(result.removed) == 1
    assert result.removed[0].reason.startswith("malformed_record:")


def test_empty_input():
    result = deduplicate([])

    assert result.records == []
    assert result.removed == []
    assert find_duplicate_groups([]) == {}


def test_invalid_duplicate_level_raises_error():
    records = [make()]

    with pytest.raises(ValueError):
        find_duplicate_groups(records, level="invalid")

    with pytest.raises(ValueError):
        deduplicate(records, level="invalid")

def test_audit_quality_with_clean_records():
    records = [
        make("Welcome", "Your account is ready", "Safe Email"),
        make("Meeting", "Meeting starts at noon", "Safe Email"),
    ]

    result = audit_quality(records, level="exact")

    assert result.total_records == 2
    assert result.invalid_records == 0
    assert result.duplicate_groups == 0
    assert result.duplicate_records == 0
    assert result.conflicting_label_groups == 0


def test_audit_quality_counts_invalid_records():
    records = [
        make("Welcome", "Your account is ready"),
        {
            "subject": None,
            "body": "Invalid subject",
            "sender": "",
            "label": "Safe Email",
        },
    ]

    result = audit_quality(records, level="exact")

    assert result.total_records == 2
    assert result.invalid_records == 1


def test_audit_quality_counts_duplicate_records():
    records = [
        make("Account Alert", "Verify your account"),
        make("Account Alert", "Verify your account"),
        make("Unique", "A different message"),
    ]

    result = audit_quality(records, level="exact")

    assert result.total_records == 3
    assert result.duplicate_groups == 1
    assert result.duplicate_records == 1
    assert result.conflicting_label_groups == 0


def test_audit_quality_detects_conflicting_labels():
    records = [
        make("Account Alert", "Verify your account", "Phishing Email"),
        make("Account Alert", "Verify your account", "Safe Email"),
    ]

    result = audit_quality(records, level="exact")

    assert result.duplicate_groups == 1
    assert result.duplicate_records == 1
    assert result.conflicting_label_groups == 1


def test_audit_quality_with_empty_input():
    result = audit_quality([])

    assert result.total_records == 0
    assert result.invalid_records == 0
    assert result.duplicate_groups == 0
    assert result.duplicate_records == 0
    assert result.conflicting_label_groups == 0
