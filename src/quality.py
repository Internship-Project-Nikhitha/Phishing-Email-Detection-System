
"""Quality checks and deterministic duplicate removal for email records."""

from dataclasses import dataclass

from src import keys

Record = dict[str, str]


def find_duplicate_groups(
    records: list[Record], level: str = "near"
) -> dict[str, list[int]]:
    """Group records that share an exact or near-duplicate content key.

    Args:
        records: Cleaned email records.
        level: "exact" for identical text or "near" for similar templates.

    Returns:
        A dictionary mapping shared content keys to record indexes.
        Groups containing only one record are excluded.

    Raises:
        ValueError: If level is unknown.
    """
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


@dataclass(frozen=True)
class RemovedRecord:
    """Audit entry for one record excluded during deduplication."""

    index: int
    record_id: str | None
    reason: str
    kept_index: int | None = None


@dataclass(frozen=True)
class DedupResult:
    """Records retained and records removed during deduplication."""

    records: list[Record]
    removed: list[RemovedRecord]


def deduplicate(
    records: list[Record], level: str = "near"
) -> DedupResult:
    """Deduplicate records without silently resolving conflicting labels.

    Records sharing a key and the same label retain their first occurrence.
    If labels conflict within a key group, every record in that group is
    excluded. Malformed records are excluded and logged.

    Missing or None subject/body fields are handled according to src.keys.
    Removal indexes refer to the original input order. The audit log does
    not contain email text.
    """
    key_function = keys.key_function(level)
    groups: dict[str, list[int]] = {}
    removed: list[RemovedRecord] = []
    valid: dict[int, tuple[str, str, str]] = {}

    for index, record in enumerate(records):
        try:
            key = key_function(record)
            rid = keys.record_id(record)
        except (TypeError, ValueError):
            removed.append(
                RemovedRecord(
                    index,
                    None,
                    "malformed_record: invalid record, subject, or body",
                )
            )
            continue

        label = record.get("label")
        if not isinstance(label, str) or not label.strip():
            removed.append(
                RemovedRecord(
                    index,
                    rid,
                    "malformed_record: missing or invalid label",
                )
            )
            continue

        valid[index] = (key, label, rid)
        groups.setdefault(key, []).append(index)

    excluded: set[int] = set()

    for indexes in groups.values():
        labels = {valid[i][1] for i in indexes}

        if len(labels) > 1:
            # Exclude the entire group; never silently choose a label.
            for i in indexes:
                excluded.add(i)
                removed.append(
                    RemovedRecord(
                        i,
                        valid[i][2],
                        "conflicting_labels: content has different labels",
                    )
                )
        else:
            # Keep the first occurrence and log subsequent duplicates.
            kept_index = indexes[0]
            for i in indexes[1:]:
                excluded.add(i)
                removed.append(
                    RemovedRecord(
                        i,
                        valid[i][2],
                        "duplicate: same content key and label",
                        kept_index,
                    )
                )

    retained = [
        record
        for i, record in enumerate(records)
        if i in valid and i not in excluded
    ]

    removed.sort(key=lambda item: item.index)

    return DedupResult(records=retained, removed=removed)
