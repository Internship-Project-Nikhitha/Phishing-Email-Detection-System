"""Tests for src/splitting.py."""

import pytest

from src import splitting as sp


def word(number):
    """A distinct letters-only word (digits would be ignored by near-duplicate keys)."""
    return "".join(chr(97 + (number // 26**place) % 26) for place in range(3))


def make_records(per_label=40, copies=1):
    records = []
    for label in ("phishing", "legitimate"):
        for number in range(per_label):
            text = f"{label} message {word(number)} {word(number + 500)}"
            for _ in range(copies):
                records.append({"subject": text, "body": f"body of {text}", "sender": "", "label": label})
    return records


@pytest.mark.parametrize("ratios", [(0.7, 0.15, 0.15), (0.6, 0.2, 0.2), (0.5, 0.25, 0.25)])
def test_validate_ratios_accepts_good_ratios(ratios):
    assert sp.validate_ratios(ratios) == ratios


@pytest.mark.parametrize(
    "ratios, message",
    [
        ((0.7, 0.3), "three numbers"),
        ((0.5, 0.5, 0.5), "add up to 1"),
        ((1.0, 0.0, 0.0), "greater than 0"),
        ((-0.1, 0.6, 0.5), "greater than 0"),
        (("a", "b", "c"), "three numbers"),
        (None, "three numbers"),
        ((float("nan"), 0.5, 0.5), "finite numbers"),
        ((float("inf"), 0.0, 0.0), "finite numbers"),
    ],
)
def test_validate_ratios_rejects_bad_ratios(ratios, message):
    with pytest.raises(ValueError, match=message):
        sp.validate_ratios(ratios)


def test_split_result_by_name_and_sizes():
    result = sp.SplitResult(train=[{"a": "1"}], validation=[], test=[{"a": "2"}, {"a": "3"}])

    assert result.sizes() == {"train": 1, "validation": 0, "test": 2}
    assert result.by_name("test") == [{"a": "2"}, {"a": "3"}]
    with pytest.raises(ValueError, match="Unknown split"):
        result.by_name("holdout")




def test_split_dataset_is_reproducible_and_has_all_partitions():
    result1 = sp.split_dataset(make_records(per_label=40), random_state=17)
    result2 = sp.split_dataset(make_records(per_label=40), random_state=17)
    assert result1 == result2
    assert all(result1.sizes()[name] > 0 for name in sp.SPLIT_NAMES)
    assert sum(result1.sizes().values()) == 80


def test_split_dataset_keeps_exact_duplicates_together():
    records = make_records(per_label=20, copies=2)
    result = sp.split_dataset(records, random_state=3)
    from src.keys import exact_key
    location = {}
    for name in sp.SPLIT_NAMES:
        for record in result.by_name(name):
            key = exact_key(record)
            assert key not in location or location[key] == name
            location[key] = name


def test_split_dataset_near_duplicate_conflicting_labels_fails_closed():
    records = [
        {"subject": "Dear user 123", "body": "Visit http://one.example.invalid/123", "label": "phishing"},
        {"subject": "Dear user 456", "body": "Visit http://two.example.invalid/456", "label": "legitimate"},
        {"subject": "ordinary lunch plan", "body": "meet at noon", "label": "legitimate"},
        {"subject": "account alert", "body": "verify account now", "label": "phishing"},
    ]
    with pytest.raises(ValueError, match="conflicting labels"):
        sp.split_dataset(records, duplicate_level="near")


def test_split_dataset_rejects_empty_and_invalid_records():
    with pytest.raises(ValueError, match="empty dataset"):
        sp.split_dataset([])
    with pytest.raises(ValueError, match="Invalid record at index 0"):
        sp.split_dataset([{"subject": "", "body": "", "label": "phishing"}])


def test_near_duplicate_leakage_assertion_detects_overlap():
    a = {"subject": "Dear user 123", "body": "Open http://a.example.invalid/123", "sender": "", "label": "phishing"}
    b = {"subject": "Dear user 456", "body": "Open http://b.example.invalid/456", "sender": "", "label": "phishing"}
    result = sp.SplitResult(train=[a], validation=[b], test=[
        {"subject": "totally different", "body": "distinct content", "sender": "", "label": "legitimate"}
    ])
    with pytest.raises(ValueError, match="Duplicate leakage"):
        sp.assert_no_duplicate_leakage(result, duplicate_level="near")
