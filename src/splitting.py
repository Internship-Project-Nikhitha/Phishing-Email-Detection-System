"""Reproducible train/validation/test splitting with duplicate-group protection.

Input records are normalized through the project's existing ``preprocess_email``
function. Duplicate groups are assigned atomically to one partition so copies
cannot leak across train, validation, and test. No email URLs are fetched.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import warnings
from dataclasses import dataclass
from typing import Iterable

from src.preprocessing import EmailValidationError, normalize_text, preprocess_email
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


@dataclass(frozen=True)
class LeakageReport:
    """Count-based, content-free summary of a split leakage audit.

    ``groups_checked`` counts distinct exact/near identity keys across all
    partitions. ``duplicate_groups_checked`` counts keys occurring more than
    once, including duplicates contained entirely within one partition.
    ``overlap_groups`` counts keys that occur in multiple partitions, and
    ``overlapping_records`` counts all records belonging to those groups.
    No record text or content key is included in the report.
    """

    duplicate_level: str
    records_checked: int
    groups_checked: int
    duplicate_groups_checked: int
    overlap_groups: int
    overlapping_records: int

    @property
    def is_leakage_free(self) -> bool:
        """Whether no identity group crosses partition boundaries."""
        return self.overlap_groups == 0


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
    """Greedily allocate whole groups toward target class counts."""
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

    for group_index, (group, label) in enumerate(group_info):
        candidate_splits = list(range(3))
        empty_splits = [s for s, part in enumerate(partitions) if not part]
        groups_remaining = len(group_info) - group_index

        # Reserve enough remaining groups to populate every empty partition.
        if empty_splits and groups_remaining <= len(empty_splits):
            candidate_splits = empty_splits

        candidates = {}
        for s in candidate_splits:
            # Prefer the partition with greatest normalized class deficit;
            # use overall size deficit as a tie-breaker.
            if stratify:
                class_deficit = (targets[s][label] - counts[s][label]) / max(targets[s][label], 1)
                score = class_deficit * 2 + (target_sizes[s] - sizes[s]) / max(target_sizes[s], 1)
            else:
                score = (target_sizes[s] - sizes[s]) / max(target_sizes[s], 1)
            candidates[s] = score
        best = max(candidate_splits, key=lambda s: (candidates[s], -s))
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
    messages; review its impact and conflicting labels before enabling it.
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


def audit_split_leakage(
    result: SplitResult, duplicate_level: str = "exact"
) -> LeakageReport:
    """Audit exact/near identity groups and return a content-free count report.

    This report checks all records in ``result`` and does not mutate the
    partitions. A group is considered leaked when its key appears in two or
    more different partitions. Repeated records wholly contained in one split
    are counted as duplicate groups but not as leakage.

    The report contains counts only; it does not expose email text or content
    keys. Use :func:`assert_no_duplicate_leakage` when leakage must raise.
    """
    if not isinstance(result, SplitResult):
        raise TypeError("result must be a SplitResult instance.")
    key_fn = key_function(duplicate_level)
    group_counts: dict[str, int] = {}
    group_splits: dict[str, set[str]] = {}
    records_checked = 0

    for split_name in SPLIT_NAMES:
        for record in result.by_name(split_name):
            key = key_fn(record)
            records_checked += 1
            group_counts[key] = group_counts.get(key, 0) + 1
            group_splits.setdefault(key, set()).add(split_name)

    leaked_keys = {
        key for key, split_names in group_splits.items() if len(split_names) > 1
    }
    return LeakageReport(
        duplicate_level=duplicate_level,
        records_checked=records_checked,
        groups_checked=len(group_counts),
        duplicate_groups_checked=sum(count > 1 for count in group_counts.values()),
        overlap_groups=len(leaked_keys),
        overlapping_records=sum(group_counts[key] for key in leaked_keys),
    )


def assert_no_duplicate_leakage(result: SplitResult, duplicate_level: str = "exact") -> None:
    """Raise ``ValueError`` if exact/near duplicate keys cross partitions.

    This backwards-compatible assertion delegates to :func:`audit_split_leakage`
    and reports the number of overlapping groups without including email text.
    """
    report = audit_split_leakage(result, duplicate_level=duplicate_level)
    if not report.is_leakage_free:
        raise ValueError(
            f"Duplicate leakage detected: {report.overlap_groups} {duplicate_level} "
            f"duplicate group(s) occur across train/validation/test splits "
            f"({report.overlapping_records} records in overlapping groups)."
        )


def fingerprint_split(result: SplitResult, duplicate_level: str = "exact") -> str:
    """Return a deterministic SHA-256 fingerprint for split identities/assignments.

    Fingerprint inputs for each record are: the selected exact/near SHA-256
    content key (based on normalized subject and body), the canonical label,
    the assigned partition name, and a SHA-256 digest of the normalized sender.
    These entries are sorted before serialization, so reordering records
    *within the same partition* does not change the fingerprint. Record
    multiplicity is retained. The returned value is only a 64-character
    hexadecimal digest; raw email text and sender values are never returned.

    The digest changes when a record's canonical identity, sender, label, or
    partition assignment changes. As with any deterministic unsalted hash, it
    is not anonymization and may be guessable for known or low-entropy inputs;
    do not use it as a substitute for access controls. The selected duplicate
    level defines identity, so changes ignored by that key's normalization may
    not change the digest. The seed and requested ratios are not independently
    encoded: the fingerprint describes the resulting records and assignments.
    """
    if not isinstance(result, SplitResult):
        raise TypeError("result must be a SplitResult instance.")
    key_fn = key_function(duplicate_level)
    entries: list[tuple[str, str, str, str]] = []

    for split_name in SPLIT_NAMES:
        for index, record in enumerate(result.by_name(split_name)):
            try:
                cleaned = preprocess_email(record)
                identity = key_fn(cleaned)
                sender_digest = hashlib.sha256(
                    normalize_text(cleaned["sender"]).casefold().encode("utf-8")
                ).hexdigest()
            except (EmailValidationError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Cannot fingerprint invalid record in {split_name} split at index {index}: {exc}"
                ) from exc
            entries.append((split_name, identity, cleaned["label"], sender_digest))

    canonical_payload = {
        "format": "phishing-split-fingerprint-v1",
        "duplicate_level": duplicate_level,
        "records": [list(entry) for entry in sorted(entries)],
    }
    serialized = json.dumps(
        canonical_payload,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()
