


"""Quality checks and deterministic duplicate removal for email records."""

from dataclasses import dataclass

from src import keys
from src.preprocessing import EmailValidationError, normalize_label

Record = dict[str, str]


@dataclass(frozen=True)
class RemovedRecord:
    """Audit entry for one excluded record."""

    index: int
    record_id: str | None
    reason: str
    kept_index: int | None = None


@dataclass(frozen=True)
class DedupResult:
    """Records retained and records removed during deduplication."""

    records: list[Record]
    removed: list[RemovedRecord]


def find_duplicate_groups(
    records: list[Record], level: str = "near"
) -> dict[str, list[int]]:
    """Return groups of records sharing an exact or near-duplicate key."""
    key_function = keys.key_function(level)
    groups: dict[str, list[int]] = {}

    for index, record in enumerate(records):
        key = key_function(record)
        groups.setdefault(key, []).append(index)

    return {
        key: indexes
        for key, indexes in groups.items()
        if len(indexes) > 1
    }


def deduplicate(
    records: list[Record], level: str = "near"
) -> DedupResult:
    """Deduplicate records and log malformed or conflicting records.

    Identical content with the same normalized label keeps its first
    occurrence. If duplicate content has conflicting labels, all records
    in that group are excluded. Malformed records are logged.
    """
    key_function = keys.key_function(level)
    groups: dict[str, list[int]] = {}
    removed: list[RemovedRecord] = []
    valid: dict[int, tuple[str, str, str]] = {}

    for index, record in enumerate(records):
        try:
            if not isinstance(record, dict):
                raise ValueError("Record must be a dictionary")

            if not isinstance(record.get("subject"), str):
                raise ValueError("Subject must be a string")

            if not isinstance(record.get("body"), str):
                raise ValueError("Body must be a string")

            key = key_function(record)
            record_id = keys.record_id(record)

        except (TypeError, ValueError, AttributeError):
            removed.append(
                RemovedRecord(
                    index=index,
                    record_id=None,
                    reason="malformed_record: invalid record, subject, or body",
                )
            )
            continue

        try:
            label = normalize_label(record.get("label"))
        except (EmailValidationError, AttributeError, TypeError):
            removed.append(
                RemovedRecord(
                    index=index,
                    record_id=record_id,
                    reason="malformed_record: missing or invalid label",
                )
            )
            continue

        valid[index] = (key, label, record_id)
        groups.setdefault(key, []).append(index)

    excluded: set[int] = set()

    for indexes in groups.values():
        labels = {valid[i][1] for i in indexes}

        if len(labels) > 1:
            for i in indexes:
                excluded.add(i)
                removed.append(
                    RemovedRecord(
                        index=i,
                        record_id=valid[i][2],
                        reason="conflicting_labels: content has different labels",
                    )
                )
        else:
            kept_index = indexes[0]

            for i in indexes[1:]:
                excluded.add(i)
                removed.append(
                    RemovedRecord(
                        index=i,
                        record_id=valid[i][2],
                        reason="duplicate: same content key and label",
                        kept_index=kept_index,
                    )
                )

    retained = [
        record
        for i, record in enumerate(records)
        if i in valid and i not in excluded
    ]

    removed.sort(key=lambda item: item.index)

    return DedupResult(records=retained, removed=removed)

@dataclass(frozen=True)
class QualityAudit:
    """Summary of dataset quality checks."""

    total_records: int
    invalid_records: int
    duplicate_groups: int
    duplicate_records: int
    conflicting_label_groups: int


def audit_quality(
    records: list[Record], level: str = "exact"
) -> QualityAudit:
    """Audit records for malformed entries, duplicates, and label conflicts.

    This function does not modify the input records. Duplicate and
    conflicting-label counts are calculated using the selected key level.
    """
    key_function = keys.key_function(level)
    groups: dict[str, list[int]] = {}
    invalid_indexes: set[int] = set()
    labels_by_index: dict[int, str] = {}

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            invalid_indexes.add(index)
            continue

        if not isinstance(record.get("subject"), str):
            invalid_indexes.add(index)
            continue

        if not isinstance(record.get("body"), str):
            invalid_indexes.add(index)
            continue

        try:
            label = normalize_label(record.get("label"))
            key = key_function(record)
        except (EmailValidationError, TypeError, ValueError, AttributeError):
            invalid_indexes.add(index)
            continue

        labels_by_index[index] = label
        groups.setdefault(key, []).append(index)

    duplicate_groups = [
        indexes for indexes in groups.values() if len(indexes) > 1
    ]

    conflicting_groups = [
        indexes
        for indexes in duplicate_groups
        if len({labels_by_index[index] for index in indexes}) > 1
    ]

    return QualityAudit(
        total_records=len(records),
        invalid_records=len(invalid_indexes),
        duplicate_groups=len(duplicate_groups),
        duplicate_records=sum(
            len(indexes) - 1 for indexes in duplicate_groups
        ),
        conflicting_label_groups=len(conflicting_groups),
    )

