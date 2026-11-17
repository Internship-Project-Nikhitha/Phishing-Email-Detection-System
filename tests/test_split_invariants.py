"""Properties that must hold for every seed, not just the default one (leakage-safe splitting)."""

import random
import warnings
from collections import Counter

import pytest

from src import keys, splitting as sp

SEEDS = [0, 1, 7, 42, 123, 2026]


def word(number):
    """A distinct letters-only word (digits are ignored by near-duplicate keys)."""
    return "".join(chr(97 + (number // 26**place) % 26) for place in range(3))


def dataset(per_label=60, duplicate_every=5, copies=3):
    """Two balanced classes; every ``duplicate_every``-th message appears ``copies`` times."""
    records = []
    for label in ("phishing", "legitimate"):
        for number in range(per_label):
            text = f"{label} message {word(number)} {word(number + 700)}"
            repeat = copies if number % duplicate_every == 0 else 1
            records += [{"subject": text, "body": f"body of {text}", "sender": "", "label": label}] * repeat
    return records


def all_records(result):
    return result.train + result.validation + result.test


@pytest.mark.parametrize("seed", SEEDS)
def test_every_record_lands_in_exactly_one_split(seed):
    records = dataset()

    result = sp.split_dataset(records, random_state=seed)

    assert sum(result.sizes().values()) == len(records)
    expected = Counter(keys.exact_key(r) for r in records)
    assert Counter(keys.exact_key(r) for r in all_records(result)) == expected


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("level", ["exact", "near"])
def test_no_duplicate_group_crosses_a_split_boundary(seed, level):
    result = sp.split_dataset(dataset(), random_state=seed, duplicate_level=level)

    report = sp.audit_split_leakage(result, duplicate_level=level)

    assert report.is_leakage_free and report.overlapping_records == 0
    assert report.duplicate_groups_checked > 0  # the data really contains duplicates


@pytest.mark.parametrize("seed", SEEDS)
def test_split_sizes_stay_close_to_the_requested_ratios(seed):
    records = dataset()
    result = sp.split_dataset(records, 0.7, 0.15, 0.15, random_state=seed)
    total = len(records)

    for name, ratio in zip(sp.SPLIT_NAMES, (0.7, 0.15, 0.15)):
        assert abs(len(result.by_name(name)) / total - ratio) < 0.08, (name, result.sizes())


@pytest.mark.parametrize("seed", SEEDS)
def test_every_split_contains_both_classes(seed):
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a missing class would raise a RuntimeWarning
        result = sp.split_dataset(dataset(), random_state=seed)

    for name in sp.SPLIT_NAMES:
        assert {r["label"] for r in result.by_name(name)} == {"phishing", "legitimate"}


@pytest.mark.parametrize("seed", SEEDS)
def test_class_balance_is_roughly_preserved_in_each_split(seed):
    result = sp.split_dataset(dataset(), random_state=seed)

    for name in sp.SPLIT_NAMES:
        labels = Counter(r["label"] for r in result.by_name(name))
        share = labels["phishing"] / sum(labels.values())
        assert 0.35 < share < 0.65, (name, labels)


@pytest.mark.parametrize("seed", SEEDS)
def test_same_seed_gives_the_same_split_and_fingerprint(seed):
    first = sp.split_dataset(dataset(), random_state=seed)
    second = sp.split_dataset(dataset(), random_state=seed)

    assert first == second
    assert sp.fingerprint_split(first) == sp.fingerprint_split(second)


def test_different_seeds_give_different_splits():
    fingerprints = {sp.fingerprint_split(sp.split_dataset(dataset(), random_state=seed)) for seed in SEEDS}

    assert len(fingerprints) > 1


def test_shuffling_the_input_does_not_break_the_invariants():
    records = dataset()
    random.Random(5).shuffle(records)

    result = sp.split_dataset(records, random_state=42)

    assert sum(result.sizes().values()) == len(records)
    assert sp.audit_split_leakage(result).is_leakage_free


def test_input_records_are_not_modified_by_splitting():
    records = dataset(per_label=30)
    before = [dict(record) for record in records]

    sp.split_dataset(records, random_state=3)

    assert records == before


def test_a_generator_input_works_like_a_list():
    records = dataset(per_label=30)

    assert sp.split_dataset(iter(records), random_state=3) == sp.split_dataset(records, random_state=3)


@pytest.mark.parametrize("ratios", [(0.8, 0.1, 0.1), (0.6, 0.2, 0.2), (0.5, 0.25, 0.25)])
def test_other_ratios_also_split_without_leakage(ratios):
    result = sp.split_dataset(dataset(), *ratios, random_state=11)

    assert sp.audit_split_leakage(result).is_leakage_free
    assert len(result.train) > len(result.validation) and len(result.train) > len(result.test)


def test_unstratified_split_still_prevents_leakage():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = sp.split_dataset(dataset(), random_state=9, stratify=False)

    assert sp.audit_split_leakage(result).is_leakage_free


def test_forced_overlap_is_detected_by_the_audit():
    result = sp.split_dataset(dataset(), random_state=1)
    leaked = sp.SplitResult(result.train, result.validation, result.test + [dict(result.train[0])])

    report = sp.audit_split_leakage(leaked)

    assert not report.is_leakage_free and report.overlap_groups >= 1
    with pytest.raises(ValueError):
        sp.assert_no_duplicate_leakage(leaked)
