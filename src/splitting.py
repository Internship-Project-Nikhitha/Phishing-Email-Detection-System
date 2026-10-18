"""Reproducible dataset splitting for phishing-email classification.

This module is designed to work with preprocessed email records containing
subject, body, sender, and label fields. Exact duplicate email content is kept
within a single split to reduce train/test leakage.

Note: This is an initial implementation. The team should confirm the final
split ratios and whether duplicate identity should include sender/subject/body.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split


DEFAULT_TEXT_COLUMNS = ("subject", "body")
DEFAULT_LABEL_COLUMN = "label"
DEFAULT_DUPLICATE_COLUMNS = ("subject", "body")


class SplitError(ValueError):
    """Raised when the input cannot be split safely."""


@dataclass(frozen=True)
class DatasetSplits:
    """The three splits, preserving original row indices."""

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {
            "train": self.train,
            "validation": self.validation,
            "test": self.test,
        }


def _content_key(row: pd.Series, columns: tuple[str, ...]) -> str:
    """Stable key for exact duplicate detection (case/punctuation preserved)."""
    parts = []
    for column in columns:
        value = row[column]
        # Normalize null values consistently, while retaining meaningful text.
        parts.append("" if pd.isna(value) else str(value).strip())
    encoded = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def split_dataset(
    df: pd.DataFrame,
    *,
    label_column: str = DEFAULT_LABEL_COLUMN,
    train_size: float = 0.70,
    validation_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
    stratify: bool = True,
    duplicate_columns: tuple[str, ...] = DEFAULT_DUPLICATE_COLUMNS,
) -> DatasetSplits:
    """Split a labeled DataFrame into train, validation, and test sets.

    Exact duplicate records according to ``duplicate_columns`` are grouped
    before splitting, so matching content keys cannot occur in multiple splits.
    Groups with conflicting labels are rejected because assigning them to
    different classes can make evaluation misleading.

    The implementation uses group-level splitting and attempts stratification
    using each group's label. It may reject small or highly imbalanced datasets
    when stratified splitting is not feasible; use a larger dataset or explicitly
    set ``stratify=False`` after documenting that choice.

    Args:
        df: DataFrame containing email text and labels.
        label_column: Name of the target label column.
        train_size, validation_size, test_size: Fractions that must sum to 1.
        random_state: Seed for repeatable split assignment.
        stratify: Whether to preserve label proportions at group level.
        duplicate_columns: Columns used to identify exact duplicate email content.

    Returns:
        DatasetSplits containing train, validation, and test DataFrames.

    Raises:
        SplitError: If input is invalid, split sizes are invalid, or the groups
            cannot be split as requested.
    """
    if not isinstance(df, pd.DataFrame):
        raise SplitError("df must be a pandas DataFrame")
    if df.empty:
        raise SplitError("Cannot split an empty DataFrame")
    if not isinstance(label_column, str) or not label_column:
        raise SplitError("label_column must be a non-empty string")
    if label_column not in df.columns:
        raise SplitError(f"Missing label column: {label_column!r}")
    if not duplicate_columns:
        raise SplitError("duplicate_columns must contain at least one column")

    needed = [label_column, *duplicate_columns]
    missing_columns = [column for column in needed if column not in df.columns]
    if missing_columns:
        raise SplitError(f"Missing required column(s): {missing_columns}")

    sizes = (train_size, validation_size, test_size)
    if any(not isinstance(size, (int, float)) or size <= 0 or size >= 1 for size in sizes):
        raise SplitError("Each split size must be greater than 0 and less than 1")
    if abs(sum(sizes) - 1.0) > 1e-8:
        raise SplitError("train_size + validation_size + test_size must equal 1.0")
    if df[label_column].isna().any():
        raise SplitError(f"Missing labels found in {label_column!r}")
    if df[list(duplicate_columns)].isna().all(axis=1).any():
        raise SplitError("Rows with no duplicate-key content cannot be safely grouped")

    work = df.copy()
    work["__split_group_key__"] = work.apply(
        lambda row: _content_key(row, tuple(duplicate_columns)), axis=1
    )

    # A duplicate content key may not carry different labels.
    label_counts = work.groupby("__split_group_key__", dropna=False)[label_column].nunique()
    conflicts = label_counts[label_counts > 1]
    if not conflicts.empty:
        raise SplitError(
            f"Found {len(conflicts)} duplicate content group(s) with conflicting labels; "
            "resolve them before splitting."
        )

    # Split one representative per duplicate group, then map all rows in that
    # group back to the same partition.
    groups = work[["__split_group_key__", label_column]].drop_duplicates(
        subset=["__split_group_key__"]
    ).reset_index(drop=True)
    if len(groups) < 3:
        raise SplitError("At least three distinct content groups are required")

    y = groups[label_column] if stratify else None
    try:
        train_groups, remaining_groups = train_test_split(
            groups,
            train_size=train_size,
            random_state=random_state,
            stratify=y,
        )
        remaining_fraction = validation_size + test_size
        test_fraction_of_remaining = test_size / remaining_fraction
        remaining_y = remaining_groups[label_column] if stratify else None
        validation_groups, test_groups = train_test_split(
            remaining_groups,
            test_size=test_fraction_of_remaining,
            random_state=random_state,
            stratify=remaining_y,
        )
    except ValueError as exc:
        raise SplitError(
            "Could not create the requested split (often due to too few examples "
            "per class or too few duplicate groups). Try a larger dataset, adjust "
            "the ratios, or set stratify=False with a documented reason."
        ) from exc

    train_keys = set(train_groups["__split_group_key__"])
    validation_keys = set(validation_groups["__split_group_key__"])
    test_keys = set(test_groups["__split_group_key__"])

    # Defensive checks: keys must be mutually exclusive.
    if train_keys & validation_keys or train_keys & test_keys or validation_keys & test_keys:
        raise SplitError("Internal error: duplicate groups overlap between splits")

    def materialize(keys: set[str]) -> pd.DataFrame:
        result = work[work["__split_group_key__"].isin(keys)].drop(
            columns=["__split_group_key__"]
        )
        return result.copy()

    splits = DatasetSplits(
        train=materialize(train_keys),
        validation=materialize(validation_keys),
        test=materialize(test_keys),
    )
    total_rows = len(splits.train) + len(splits.validation) + len(splits.test)
    if total_rows != len(df):
        raise SplitError("Internal error: some rows were lost or duplicated during splitting")

    return splits
