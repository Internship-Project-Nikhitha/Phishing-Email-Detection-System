


"""Quality checks and deterministic duplicate removal for email records."""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from src import keys
from src.preprocessing import EmailValidationError, normalize_label

Record = dict[str, str]

_EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
_HTML_RE = re.compile(r"(?is)<\s*(?:!doctype\b|/?[a-z][a-z0-9:-]*\b[^>]*>)")
_IPV4_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
_PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d ().-]{7,}\d(?!\w)")


def _record_text(record: Record) -> tuple[str, str]:
    if not isinstance(record, dict):
        raise TypeError(f"Record must be a dict, got {type(record).__name__}.")
    values = []
    for field in ("subject", "body", "sender"):
        value = record.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise TypeError(f"Field '{field}' must be a string.")
        values.append(value)
    return values[0] + "\n" + values[1], "\n".join(values)


def audit_dataset(
    records: list[Record],
    *,
    train: list[Record] | None = None,
    test: list[Record] | None = None,
    group_field: str | None = None,
) -> dict[str, Any]:
    """Return content-safe quality counts without exposing email text."""
    if not isinstance(records, list):
        raise TypeError("records must be a list.")
    if (train is None) != (test is None):
        raise ValueError("train and test must either both be provided or both be omitted.")
    if group_field is not None and (train is None or test is None):
        raise ValueError("group_field requires both train and test records.")

    label_counts: Counter[str] = Counter()
    invalid_label_rows = 0
    empty_text_rows = 0
    duplicate_keys: Counter[str] = Counter()
    email_rows = 0
    url_rows = 0
    ipv4_rows = 0
    phone_rows = 0
    html_rows = 0

    for record in records:
        email_text, scanned_text = _record_text(record)
        if not email_text.strip():
            empty_text_rows += 1
        duplicate_keys[keys.exact_key(record)] += 1
        try:
            label_counts[normalize_label(record.get("label"))] += 1
        except EmailValidationError:
            invalid_label_rows += 1
        email_rows += bool(_EMAIL_RE.search(scanned_text))
        url_rows += bool(_URL_RE.search(scanned_text))
        ipv4_rows += bool(_IPV4_RE.search(scanned_text))
        phone_rows += bool(_PHONE_RE.search(scanned_text))
        html_rows += bool(_HTML_RE.search(scanned_text))

    nonzero_classes = [count for count in label_counts.values() if count]
    imbalance = (
        float(max(nonzero_classes) / min(nonzero_classes))
        if len(nonzero_classes) == 2
        else None
    )
    report: dict[str, Any] = {
        "rows": len(records),
        "empty_text_rows": empty_text_rows,
        "exact_duplicate_text_rows": sum(
            count - 1 for count in duplicate_keys.values() if count > 1
        ),
        "invalid_label_rows": invalid_label_rows,
        "label_distribution": {
            label: label_counts.get(label, 0) for label in ("phishing", "legitimate")
        },
        "class_imbalance_ratio": imbalance,
        "email_address_rows": email_rows,
        "url_rows": url_rows,
        "ipv4_address_rows": ipv4_rows,
        "phone_like_rows": phone_rows,
        "html_rows": html_rows,
        "html_is_preserved": True,
        "url_is_preserved": True,
    }

    if train is not None and test is not None:
        if not isinstance(train, list) or not isinstance(test, list):
            raise TypeError("train and test must be lists.")
        if group_field is not None and not isinstance(group_field, str):
            raise TypeError("group_field must be a string.")
        train_keys = {keys.exact_key(record) for record in train}
        test_keys = {keys.exact_key(record) for record in test}
        report["train_test_exact_duplicate_emails"] = len(train_keys & test_keys)
        if group_field is not None:
            train_groups = {
                str(record[group_field])
                for record in train
                if group_field in record and record[group_field] is not None
            }
            test_groups = {
                str(record[group_field])
                for record in test
                if group_field in record and record[group_field] is not None
            }
            if any(group_field not in record for record in (*train, *test)):
                raise ValueError(f"Group field '{group_field}' must exist in every record.")
            report["group_overlap_count"] = len(train_groups & test_groups)

    return report


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
