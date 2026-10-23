"""Reproducible train/validation/test splitting with duplicate-group protection.

Input records are normalized through the project's existing ``preprocess_email``
function. Duplicate groups are assigned atomically to one partition so copies
cannot leak across train, validation, and test. No email URLs are fetched.
"""
from __future__ import annotations

import math
import random
import warnings
from dataclasses import dataclass
from typing import Iterable

from src.preprocessing import EmailValidationError, preprocess_email
from src.keys import key_function

Record = dict[str, str]
SPLIT_NAMES = ("train", "validation", "test")


@dataclass(frozen=True)
class SplitResult:
    """The three partitions of a normalized dataset."""
    train: list[Record]
    validation: list[Record]
    test: list[Record]

    def by_name(self, name: str) -> list[Record]:
        if name not in SPLIT_NAMES:
            raise ValueError(f"Unknown split {name!r}. Use one of: {', '.join(SPLIT_NAMES)}.")
        return getattr(self, name)

    def sizes(self) -> dict[str, int]:
        return {name: len(self.by_name(name)) for name in SPLIT_NAMES}


def validate_ratios(ratios: tuple[float, float, float]) -> tuple[float, float, float]:
    """Validate positive train/validation/test ratios that sum to one."""
    try:
        values = tuple(float(value) for value in ratios)
    except (TypeError, ValueError):
        raise ValueError("Ratios must be three numbers, e.g. (0.7, 0.15, 0.15).") from None
    if len(values) != 3:
        raise ValueError("Ratios must be three numbers (train, validation, test).")
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Ratios must be finite numbers.")
    if any(value <= 0 for value in values):
        raise ValueError("Every ratio must be greater than 0.")
    if abs(sum(values) - 1.0) > 1e-6:
        raise ValueError(f"Ratios must add up to 1, got {sum(values):.4f}.")
    return values  # type: ignore[return-value]


def _group_records(records: list[Record], duplicate_level: str) -> list[list[int]]:
    """Build duplicate-key groups; every record belongs to one group."""
    key_fn = key_function(duplicate_level)
    buckets: dict[str, list[int]] = {}
    for i, record in enumerate(records):
        buckets.setdefault(key_fn(record), []).append(i)
    return list(buckets.values())


def _allocate_groups(groups: list[list[int]], records: list[Record],
                     ratios: tuple[float, float, float], seed: int,
                     stratify: bool) -> list[list[int]]:
    """Greedily allocate whole groups toward target class counts.

    Groups are indivisible, so this balances toward (rather than guarantees)
    the requested ratios. A group containing more than one label is rejected
    before any partition is assigned.
    """
    rng = random.Random(seed)
    # Each group is represented by its class-count vector. Mixed-label groups
    # are invalid: assigning them atomically would make class stratification
    # ambiguous and can indicate a conflicting-label duplicate.
    group_info = []
    for group in groups:
        labels = {records[i]["label"] for i in group}
        if len(labels) != 1:
            raise ValueError(
                "Duplicate group contains conflicting labels; resolve conflicting-label "
                "duplicates before splitting; exact duplicates can also have conflicting labels."
            )
        label = next(iter(labels))
        group_info.append((group, label))
    rng.shuffle(group_info)
    # Larger groups first reduces the chance that a large duplicate family
    # causes severe deviation from target sizes.
    group_info.sort(key=lambda item: len(item[0]), reverse=True)

    labels = ("phishing", "legitimate")
    totals = {label: sum(len(g) for g, lab in group_info if lab == label) for label in labels}
    targets = [{label: totals[label] * ratios[s] for label in labels} for s in range(3)]
    counts = [{label: 0 for label in labels} for _ in range(3)]
    sizes = [0, 0, 0]
    target_sizes = [len(records) * ratio for ratio in ratios]
    partitions: list[list[int]] = [[], [], []]

    for group, label in group_info:
        candidates = []
        for s in range(3):
            # Prefer the partition with greatest normalized class deficit;
            # use overall size deficit as a tie-breaker.
            if stratify:
                class_deficit = (targets[s][label] - counts[s][label]) / max(targets[s][label], 1)
                score = class_deficit * 2 + (target_sizes[s] - sizes[s]) / max(target_sizes[s], 1)
            else:
                score = (target_sizes[s] - sizes[s]) / max(target_sizes[s], 1)
            candidates.append(score)
        best = max(range(3), key=lambda s: (candidates[s], -s))
        partitions[best].extend(group)
        sizes[best] += len(group)
        counts[best][label] += len(group)
    for part in partitions:
        rng.shuffle(part)
    return partitions


def split_dataset(
    records: Iterable[dict],
    train_size: float = 0.70,
    validation_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
    stratify: bool = True,
    duplicate_level: str = "exact",
) -> SplitResult:
    """Preprocess and split records while preventing duplicate leakage.

    ``duplicate_level`` is ``"exact"`` (recommended default) or ``"near"``.
    Near grouping is more conservative and may merge unrelated template-like
    messages; review its impact before enabling it. Groups are never divided
    across partitions, and a group with conflicting labels raises ``ValueError``
    rather than being silently assigned.

    The requested ratios are targets, not guarantees: indivisible groups and
    very small datasets can make exact proportions impossible. At least three
    assignable groups are needed to populate all three partitions; if the
    resulting split has an empty partition, this function raises ``ValueError``
    instead of returning an incomplete result.
    """
    ratios = validate_ratios((train_size, validation_size, test_size))
    if isinstance(random_state, bool) or not isinstance(random_state, int):
        raise ValueError("random_state must be an integer.")
    key_function(duplicate_level)  # validate level before processing
    try:
        raw_records = list(records)
    except TypeError:
        raise ValueError("records must be an iterable of email record dictionaries.") from None
    if not raw_records:
        raise ValueError("Cannot split an empty dataset.")

    cleaned: list[Record] = []
    for index, record in enumerate(raw_records):
        try:
            cleaned.append(preprocess_email(record))
        except (EmailValidationError, TypeError) as exc:
            raise ValueError(f"Invalid record at index {index}: {exc}") from exc

    groups = _group_records(cleaned, duplicate_level)
    partitions = _allocate_groups(groups, cleaned, ratios, random_state, stratify)
    result = SplitResult(*( [cleaned[i] for i in part] for part in partitions ))
    if not result.train or not result.validation or not result.test:
        raise ValueError(
            "The dataset/duplicate groups are too small to populate all three splits; "
            "add more independent records or reduce the number of partitions."
        )
    if stratify:
        all_labels = {record["label"] for record in cleaned}
        for split_name in SPLIT_NAMES:
            split_labels = {
                record["label"] for record in result.by_name(split_name)
            }
            missing_labels = sorted(all_labels - split_labels)
            if missing_labels:
                warnings.warn(
                    f"The {split_name} split contains no records for class(es) "
                    f"{missing_labels}; class-specific evaluation may be unreliable. "
                    "This can happen with rare classes or duplicate groups.",
                    RuntimeWarning,
                    stacklevel=2,
                )

    assert_no_duplicate_leakage(result, duplicate_level=duplicate_level)
    return result


def assert_no_duplicate_leakage(result: SplitResult, duplicate_level: str = "exact") -> None:
    """Raise ValueError if duplicate keys occur in more than one partition."""
    key_fn = key_function(duplicate_level)
    seen: dict[str, str] = {}
    for split_name in SPLIT_NAMES:
        for record in result.by_name(split_name):
            key = key_fn(record)
            previous = seen.get(key)
            if previous is not None and previous != split_name:
                raise ValueError(
                    f"Duplicate leakage detected: a {duplicate_level} duplicate occurs in "
                    f"both {previous!r} and {split_name!r}."
                )
            seen[key] = split_name
