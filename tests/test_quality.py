


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

def test_audit_reports_valid_and_invalid_records():
    records = [
        make("Welcome", "Account ready", "legitimate"),
        make("", "   ", "legitimate"),
        make("Warning", "Verify account", "invalid-label"),
    ]

    result = audit_quality(records)

    assert result.total_records == 3
    assert result.valid_records == 1
    assert result.invalid_records == 2
    assert result.missing_content_records == 1
    assert result.invalid_label_records == 1


def test_audit_reports_exact_and_near_duplicates():
    records = [
        make("Invoice 123", "Please visit https://example.com"),
        make("Invoice 456", "Please visit https://another.com"),
        make("Unique", "Different message"),
    ]

    result = audit_quality(records)

    assert result.exact_duplicate_groups == 0
    assert result.exact_duplicate_records == 0
    assert result.near_duplicate_groups == 1
    assert result.near_duplicate_records == 1


def test_audit_preserves_legacy_duplicate_fields():
    records = [
        make("Account Alert", "Verify your account", "legitimate"),
        make("Account Alert", "Verify your account", "phishing"),
    ]

    result = audit_quality(records, level="exact")

    assert result.duplicate_groups == result.exact_duplicate_groups == 1
    assert result.duplicate_records == result.exact_duplicate_records == 1
    assert result.conflicting_label_groups == 1


def test_audit_does_not_mutate_input():
    records = [
        make("Account Alert", "Verify your account", "legitimate"),
        make("Account Alert", "Verify your account", "legitimate"),
    ]
    original = [record.copy() for record in records]

    audit_quality(records)

    assert records == original

def test_audit_counts_invalid_label_on_malformed_record():
    result = audit_quality([
        {
            "subject": None,
            "body": "Example message",
            "label": "not-a-valid-label",
        }
    ])

    assert result.invalid_records == 1
    assert result.invalid_label_records == 1
    assert result.valid_records == 0