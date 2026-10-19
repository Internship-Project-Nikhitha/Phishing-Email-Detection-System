"""Load and normalize locally stored email classification datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


class DatasetLoadError(ValueError):
    """Raised when a dataset cannot be safely loaded or configured."""


@dataclass
class DatasetLoadResult:
    dataframe: pd.DataFrame
    summary: dict[str, Any]
    invalid_rows: pd.DataFrame


def _read_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return pd.read_csv(path)
        if suffix == ".json":
            return pd.read_json(path)
        if suffix == ".jsonl":
            return pd.read_json(path, lines=True)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, pd.errors.ParserError) as exc:
        raise DatasetLoadError(f"Could not parse dataset file '{path.name}': {exc}") from exc
    raise DatasetLoadError(
        f"Unsupported dataset format '{suffix or '<none>'}'. Supported formats: .csv, .json, .jsonl."
    )


def _normalized_key(value: Any) -> str | None:
    if not pd.api.types.is_scalar(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None
    return str(value).strip().casefold() or None


def load_dataset(
    path: str | Path,
    *,
    label_mapping: Mapping[str, str],
    column_mapping: Mapping[str, str] | None = None,
    source_column: str | None = None,
    remove_duplicates: bool = True,
) -> DatasetLoadResult:
    """Load emails, apply an explicit source-label map, and redact invalid-row details.

    ``column_mapping`` maps canonical names (``text``, ``label``) to source
    columns. Label keys are case-insensitive after trimming. Invalid row reports
    contain source row numbers and reasons only, never email content.
    """
    dataset_path = Path(path).expanduser()
    if not dataset_path.is_file():
        raise DatasetLoadError(f"Dataset file does not exist or is not a file: {dataset_path}")
    if not label_mapping:
        raise DatasetLoadError("An explicit label_mapping is required; source labels are never guessed.")

    normalized_mapping: dict[str, str] = {}
    for source_label, target_label in label_mapping.items():
        key = _normalized_key(source_label)
        target = _normalized_key(target_label)
        if key is None or target not in {"phishing", "legitimate"}:
            raise DatasetLoadError(
                "label_mapping values must be 'phishing' or 'legitimate', with non-empty source labels."
            )
        normalized_mapping[key] = target
    if len(normalized_mapping) != len(label_mapping):
        raise DatasetLoadError("label_mapping contains duplicate source labels after normalization.")

    raw = _read_file(dataset_path)
    source_row_offset = 2 if dataset_path.suffix.lower() == ".csv" else 1
    if raw.empty and len(raw.columns) == 0:
        raise DatasetLoadError("Dataset file contains no header or records.")
    mapping = dict(column_mapping or {})
    text_column = mapping.get("text", "text")
    label_column = mapping.get("label", "label")
    if text_column not in raw.columns or label_column not in raw.columns:
        missing = [name for name in (text_column, label_column) if name not in raw.columns]
        raise DatasetLoadError(
            f"Required source column(s) missing: {missing}. Available columns: {list(raw.columns)}"
        )
    if source_column is not None and source_column not in raw.columns:
        raise DatasetLoadError(f"Configured source column '{source_column}' is not present in the dataset.")

    result = raw.copy()
    result["source_label"] = raw[label_column]
    text_values = raw[text_column]
    missing_value = text_values.map(
        lambda value: pd.api.types.is_scalar(value) and bool(pd.isna(value))
    )
    string_value = text_values.map(lambda value: isinstance(value, str))
    result["text"] = text_values.map(lambda value: value if isinstance(value, str) else "")
    result["label"] = raw[label_column].map(
        lambda value: normalized_mapping.get(_normalized_key(value))
    )
    result["source"] = raw[source_column] if source_column else dataset_path.name

    invalid: list[dict[str, Any]] = []
    empty_text = string_value & result["text"].str.strip().eq("")
    missing_text = missing_value | empty_text
    malformed_text = ~missing_value & ~string_value
    unknown_label = result["label"].isna()
    for index in result.index[missing_text]:
        invalid.append({"source_row": int(index) + source_row_offset, "reason": "missing_or_empty_text"})
    for index in result.index[malformed_text]:
        invalid.append({"source_row": int(index) + source_row_offset, "reason": "malformed_text"})
    for index in result.index[unknown_label]:
        invalid.append({"source_row": int(index) + source_row_offset, "reason": "unknown_or_missing_label"})

    valid_mask = ~missing_text & ~malformed_text & ~unknown_label
    valid = result.loc[valid_mask].copy()
    conflicting = valid.groupby("text", sort=False)["label"].nunique()
    conflict_text = set(conflicting[conflicting > 1].index)
    if conflict_text:
        conflict_indices = valid.index[valid["text"].isin(conflict_text)]
        for index in conflict_indices:
            invalid.append(
                {"source_row": int(index) + source_row_offset, "reason": "duplicate_text_conflicting_labels"}
            )
        valid = valid.loc[~valid["text"].isin(conflict_text)].copy()

    duplicate_count = int(valid.duplicated(subset=["text"], keep="first").sum())
    if remove_duplicates:
        valid = valid.drop_duplicates(subset=["text"], keep="first")

    distribution = valid["label"].value_counts().reindex(
        ["phishing", "legitimate"], fill_value=0
    )
    nonzero = distribution[distribution > 0]
    imbalance_ratio = (
        float(nonzero.max() / nonzero.min()) if len(nonzero) == 2 else None
    )
    invalid_frame = pd.DataFrame(invalid, columns=["source_row", "reason"])
    summary = {
        "input_rows": int(len(raw)),
        "output_rows": int(len(valid)),
        "removed_invalid_rows": int(len(invalid_frame)),
        "missing_or_empty_text_rows": int(missing_text.sum()),
        "malformed_text_rows": int(malformed_text.sum()),
        "unknown_or_missing_label_rows": int(unknown_label.sum()),
        "conflicting_duplicate_rows": int(sum(
            row["reason"] == "duplicate_text_conflicting_labels" for row in invalid
        )),
        "exact_duplicate_rows": duplicate_count,
        "duplicates_removed": duplicate_count if remove_duplicates else 0,
        "label_distribution": {key: int(value) for key, value in distribution.items()},
        "class_imbalance_ratio": imbalance_ratio,
        "source_column": source_column,
        "removed_duplicates": bool(remove_duplicates),
    }
    return DatasetLoadResult(valid.reset_index(drop=True), summary, invalid_frame)