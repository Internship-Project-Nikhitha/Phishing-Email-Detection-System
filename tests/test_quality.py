
import pytest

from src.quality import deduplicate, find_duplicate_groups


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




def test_deduplicate_empty_and_singleton():
    from src.quality import deduplicate

    assert deduplicate([]).records == []

    record = make("Unique", "Message")
    result = deduplicate([record])

    assert result.records == [record]
    assert result.removed == []


def test_deduplicate_same_label_keeps_first():
    from src.quality import deduplicate

    first = make("Hello", "World", "legitimate")
    duplicate = make("hello", " world ", "legitimate")

    result = deduplicate([first, duplicate], level="exact")

    assert result.records == [first]
    assert result.removed[0].index == 1
    assert result.removed[0].kept_index == 0


def test_deduplicate_conflicting_labels():
    from src.quality import deduplicate

    legitimate = make("Account Alert", "Verify now", "legitimate")
    phishing = make("account alert", " verify now ", "phishing")

    result = deduplicate([legitimate, phishing], level="exact")

    assert result.records == []
    assert len(result.removed) == 2
    assert all(
        item.reason.startswith("conflicting_labels:")
        for item in result.removed
    )


def test_deduplicate_malformed_record():
    from src.quality import deduplicate

    valid = make("Valid", "Message")
    missing_label = {"subject": "No label", "body": "Message"}

    result = deduplicate([valid, missing_label])

    assert result.records == [valid]
    assert result.removed[0].index == 1
    assert result.removed[0].reason.startswith("malformed_record:")


def test_deduplicate_is_deterministic():
    from src.quality import deduplicate

    records = [
        make("A", "Same", "legitimate"),
        make("A", "Same", "legitimate"),
    ]

    first = deduplicate(records, level="exact")
    second = deduplicate(records, level="exact")

    assert first == second

def test_deduplicate_normalizes_label_variants():
    records = [
        {
            "subject": "Account alert",
            "body": "Verify account 123",
            "label": "Phishing",
        },
        {
            "subject": "Account alert",
            "body": "Verify account 123",
            "label": "phishing",
        },
    ]

    result = deduplicate(records)

    assert len(result.records) == 1
    assert result.records[0] == records[0]
    assert len(result.removed) == 1
    assert result.removed[0].reason == (
        "duplicate: same content key and label"
    )

