
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
