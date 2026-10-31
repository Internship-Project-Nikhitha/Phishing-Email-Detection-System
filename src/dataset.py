"""Validate and load configuration for a labeled email CSV dataset.

This module currently validates the configuration schema and reads a JSON
configuration file. CSV row loading and preprocessing are separate steps.
"""

import codecs
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.preprocessing import BatchResult, RecordError, preprocess_emails

COLUMN_FIELDS = ("subject", "body", "sender", "label")
LABEL_TARGETS = ("phishing", "legitimate")
_CONFIG_KEYS = ("path", "columns", "label_map", "delimiter", "encoding", "max_rows")


class DatasetError(ValueError):
    """Raised when the dataset config or the dataset file is invalid."""


@dataclass(frozen=True)
class DatasetConfig:
    """Where a dataset lives and how its columns map to email fields.

    Attributes:
        path: CSV file path (relative paths are resolved from the working
            directory, or from ``base_dir`` when one is given).
        columns: Maps ``subject``/``body``/``sender``/``label`` to the column
            names used in the CSV. ``label`` is required, and at least one of
            ``subject`` or ``body`` is required.
        label_map: Optional map from raw label text (case-insensitive) to
            ``"phishing"`` or ``"legitimate"``, applied before normalization.
        delimiter: One-character CSV delimiter.
        encoding: Text encoding of the file.
        max_rows: Optional limit on the number of data rows read.
    """

    path: str
    columns: dict[str, str]
    label_map: dict[str, str] = field(default_factory=dict)
    delimiter: str = ","
    encoding: str = "utf-8-sig"
    max_rows: int | None = None


def parse_config(data: Any) -> DatasetConfig:
    """Validate a JSON-style object and turn it into a ``DatasetConfig``.

    Args:
        data: The object loaded from the config JSON (should be a dict).

    Returns:
        A validated ``DatasetConfig``.

    Raises:
        DatasetError: If anything is missing, unknown or has the wrong type.
    """
    if not isinstance(data, dict):
        raise DatasetError(f"Dataset config must be a JSON object, got {type(data).__name__}.")

    unknown = sorted(set(data) - set(_CONFIG_KEYS))
    if unknown:
        raise DatasetError(f"Unknown config keys: {unknown}. Allowed keys: {list(_CONFIG_KEYS)}.")

    path = data.get("path")
    if not isinstance(path, str) or not path.strip():
        raise DatasetError("Config 'path' must be a non-empty string.")

    columns = data.get("columns")
    if not isinstance(columns, dict) or not columns:
        raise DatasetError("Config 'columns' must be an object mapping email fields to column names.")
    unknown_fields = sorted(set(columns) - set(COLUMN_FIELDS))
    if unknown_fields:
        raise DatasetError(f"Unknown fields in 'columns': {unknown_fields}. Allowed: {list(COLUMN_FIELDS)}.")
    for field_name, column in columns.items():
        if not isinstance(column, str) or not column.strip():
            raise DatasetError(f"Column name for '{field_name}' must be a non-empty string.")
    if "label" not in columns:
        raise DatasetError("Config 'columns' must include 'label'.")
    if "subject" not in columns and "body" not in columns:
        raise DatasetError("Config 'columns' must include at least one of 'subject' or 'body'.")

    label_map = data.get("label_map", {})
    if not isinstance(label_map, dict):
        raise DatasetError("Config 'label_map' must be an object.")
    for raw, target in label_map.items():
        if target not in LABEL_TARGETS:
            raise DatasetError(
                f"label_map value for {raw!r} must be one of {list(LABEL_TARGETS)}, got {target!r}."
            )

    delimiter = data.get("delimiter", ",")
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise DatasetError("Config 'delimiter' must be a single character.")

    encoding = data.get("encoding", "utf-8-sig")
    if not isinstance(encoding, str):
        raise DatasetError("Config 'encoding' must be a string.")
    try:
        codecs.lookup(encoding)
    except LookupError:
        raise DatasetError(f"Unknown encoding {encoding!r}.") from None

    max_rows = data.get("max_rows")
    if max_rows is not None and (isinstance(max_rows, bool) or not isinstance(max_rows, int) or max_rows < 1):
        raise DatasetError("Config 'max_rows' must be null or a positive integer.")

    return DatasetConfig(
        path=path,
        columns=dict(columns),
        label_map=dict(label_map),
        delimiter=delimiter,
        encoding=encoding,
        max_rows=max_rows,
    )


def load_config(config_path: str | Path) -> DatasetConfig:
    """Read a JSON config file and return a validated ``DatasetConfig``.

    Raises:
        DatasetError: If the file is missing, is not valid JSON, or is invalid.
    """
    path = Path(config_path)
    if not path.is_file():
        raise DatasetError(f"Config file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DatasetError(f"Config file {path} is not valid JSON: {error}") from error
    return parse_config(data)

def load_dataset(
    config: DatasetConfig | str | Path,
    *,
    base_dir: str | Path | None = None,
) -> BatchResult:
    """Load a configured CSV file and preprocess its email records."""
    if not isinstance(config, DatasetConfig):
        config = load_config(config)

    path = Path(config.path)
    if not path.is_absolute() and base_dir is not None:
        path = Path(base_dir) / path

    if not path.is_file():
        raise DatasetError(f"Dataset file not found: {path}")

    records = []
    label_map = {
        raw.strip().casefold(): target
        for raw, target in config.label_map.items()
    }

    try:
        with path.open("r", encoding=config.encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=config.delimiter, strict=True)

            if not reader.fieldnames:
                raise DatasetError("Dataset CSV has no header row.")

            if len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise DatasetError("Dataset CSV contains duplicate column names.")

            missing = sorted(set(config.columns.values()) - set(reader.fieldnames))
            if missing:
                raise DatasetError(
                    f"Dataset CSV is missing configured columns: {missing}"
                )

            rows_read = 0

            for row_number, row in enumerate(reader, start=2):
                if None in row:
                    raise DatasetError(
                        f"Dataset row {row_number} has more values than the header."
                    )

                if all(value is None or not value.strip() for value in row.values()):
                    continue

                if config.max_rows is not None and rows_read >= config.max_rows:
                    break

                rows_read += 1
                record = {
                    field: row.get(config.columns[field], "")
                    for field in ("subject", "body", "sender")
                    if field in config.columns
                }
                record["label"] = row.get(config.columns["label"], "")

                raw_label = record["label"]
                if isinstance(raw_label, str):
                    record["label"] = label_map.get(
                        raw_label.strip().casefold(), raw_label
                    )

                records.append(record)

    except DatasetError:
        raise
    except (OSError, UnicodeError, csv.Error) as error:
        raise DatasetError(f"Could not read dataset file {path}: {error}") from error

    if not records:
        raise DatasetError("Dataset CSV contains no data rows.")

    return preprocess_emails(records)


def categorize_error(message: str) -> str:
    """Group a validation message into a short reason for summary tables."""
    if message.startswith("Unknown label"):
        return "unknown label"
    if message.startswith("Label is"):
        return "missing or empty label"
    if "no usable content" in message:
        return "no usable content"
    if "must be a string" in message:
        return "wrong field type"
    return "other"


def count_error_reasons(errors: list[RecordError]) -> dict[str, int]:
    """Count rejected rows by short reason (see ``categorize_error``)."""
    counts: dict[str, int] = {}
    for error in errors:
        reason = categorize_error(error.message)
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))
