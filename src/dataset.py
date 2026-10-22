"""Validate and load configuration for a labeled email CSV dataset.

This module currently validates the configuration schema and reads a JSON
configuration file. CSV row loading and preprocessing are separate steps.
"""

import codecs
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any



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


