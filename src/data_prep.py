"""End-to-end dataset preparation: load, remove duplicates, and split."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.dataset import DatasetConfig, load_dataset
from src.preprocessing import RecordError
from src.quality import DedupResult, deduplicate, find_duplicate_groups
from src.splitting import SplitResult, split_dataset


@dataclass(frozen=True)
class PreparedData:
    """All outputs produced while preparing a dataset."""

    records: list[dict[str, str]]
    errors: list[RecordError]
    duplicate_groups: dict[str, list[int]]
    splits: SplitResult
    dedup: DedupResult | None = None

    @property
    def valid_count(self) -> int:
        """Number of records that passed preprocessing."""
        return len(self.records)

    @property
    def invalid_count(self) -> int:
        """Number of records rejected during preprocessing."""
        return len(self.errors)

    def sizes(self) -> dict[str, int]:
        """Return the number of records in each split."""
        return self.splits.sizes()


def prepare_splits(
    config: DatasetConfig | str | Path,
    *,
    base_dir: str | Path | None = None,
    train_size: float = 0.70,
    validation_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
    stratify: bool = True,
    duplicate_level: str = "exact",
) -> PreparedData:
    """Load and preprocess a dataset, remove duplicates, and create splits.

    Invalid records are retained in ``errors`` and excluded from splitting.
    ``records`` and ``duplicate_groups`` describe the valid records *before*
    duplicate removal (groups use indexes into ``records``). Duplicate
    records and records whose duplicates carry conflicting labels are removed
    by ``quality.deduplicate`` before splitting; ``dedup.removed`` lists them.
    The splitter then keeps any remaining key groups inside one partition.

    Raises:
        DatasetError: If the configuration or dataset cannot be loaded.
        ValueError: If the valid records cannot be split safely.
    """
    batch = load_dataset(config, base_dir=base_dir)
    records = batch.valid

    duplicate_groups = find_duplicate_groups(
        records,
        level=duplicate_level,
    )

    dedup = deduplicate(records, level=duplicate_level)

    splits = split_dataset(
        dedup.records,
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
        duplicate_level=duplicate_level,
    )

    return PreparedData(
        records=records,
        errors=batch.errors,
        duplicate_groups=duplicate_groups,
        splits=splits,
        dedup=dedup,
    )
