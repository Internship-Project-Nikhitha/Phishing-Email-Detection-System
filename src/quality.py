


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
    valid_records: int
    missing_content_records: int
    invalid_label_records: int
    exact_duplicate_groups: int
    exact_duplicate_records: int
    near_duplicate_groups: int
    near_duplicate_records: int


def audit_quality(
    records: list[Record], level: str = "exact"
) -> QualityAudit:
    """Audit dataset quality without modifying the input records.

    Legacy duplicate fields use the selected level. Exact and near
    duplicate metrics are also reported independently.
    """
    selected_key = keys.key_function(level)
    exact_key = keys.key_function("exact")
    near_key = keys.key_function("near")

    valid_indexes: list[int] = []
    labels: dict[int, str] = {}
    invalid_indexes: set[int] = set()
    missing_content = 0
    invalid_labels = 0

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            invalid_indexes.add(index)
            continue

        subject = record.get("subject")
        body = record.get("body")
        fields_valid = isinstance(subject, str) and isinstance(body, str)

        has_content = (
            fields_valid and bool(subject.strip() or body.strip())
        )

        if not fields_valid:
            invalid_indexes.add(index)
        elif not has_content:
            missing_content += 1
            invalid_indexes.add(index)

        try:
            label = normalize_label(record.get("label"))
        except (EmailValidationError, TypeError, ValueError, AttributeError):
            invalid_labels += 1
            invalid_indexes.add(index)
            continue

        if not fields_valid or not has_content:
            continue

        labels[index] = label
        valid_indexes.append(index)

    def summarize(key_function):
        groups: dict[str, list[int]] = {}

        for index in valid_indexes:
            key = key_function(records[index])
            groups.setdefault(key, []).append(index)

        duplicate_groups = [
            indexes for indexes in groups.values() if len(indexes) > 1
        ]
        group_count = len(duplicate_groups)
        record_count = sum(
            len(indexes) - 1 for indexes in duplicate_groups
        )
        conflicts = sum(
            len({labels[index] for index in indexes}) > 1
            for indexes in duplicate_groups
        )

        return group_count, record_count, conflicts

    selected_groups, selected_records, conflicts = summarize(selected_key)
    exact_groups, exact_records, _ = summarize(exact_key)
    near_groups, near_records, _ = summarize(near_key)

    return QualityAudit(
        total_records=len(records),
        invalid_records=len(invalid_indexes),
        duplicate_groups=selected_groups,
        duplicate_records=selected_records,
        conflicting_label_groups=conflicts,
        valid_records=len(valid_indexes),
        missing_content_records=missing_content,
        invalid_label_records=invalid_labels,
        exact_duplicate_groups=exact_groups,
        exact_duplicate_records=exact_records,
        near_duplicate_groups=near_groups,
        near_duplicate_records=near_records,
    )

