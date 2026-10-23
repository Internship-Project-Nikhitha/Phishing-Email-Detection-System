
import pytest

from src.quality import find_duplicate_groups


def make(subject="Hello", body="World", label="legitimate"):
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


def test_unique_records_are_excluded():
    records = [
        make("First subject", "First body"),
        make("Second subject", "Second body"),
    ]

    assert find_duplicate_groups(records) == {}


def test_all_duplicate_groups_keep_original_indexes():
    records = [
        make("A", "Same message"),
        make("B", "Other message"),
        make("A", "Same message"),
        make("B", "Other message"),
    ]

    groups = find_duplicate_groups(records, level="exact")

    assert sorted(sorted(indexes) for indexes in groups.values()) == [
        [0, 2],
        [1, 3],
    ]


def test_empty_records_return_no_groups():
    assert find_duplicate_groups([]) == {}


def test_unknown_level_raises_value_error():
    with pytest.raises(ValueError, match="Unknown key level"):
        find_duplicate_groups([make()], level="fuzzy")

