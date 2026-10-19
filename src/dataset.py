
"""Load CSV email datasets and reuse the existing preprocessing module."""

import csv
from pathlib import Path

import pandas as pd

from src.preprocessing import (
    EmailValidationError,
    OUTPUT_FIELDS,
    preprocess_emails,
)


class DatasetValidationError(ValueError):
    """Raised when a dataset file or its schema is invalid."""


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load and validate a CSV containing labeled email records.

    Expected columns:
        - label (required)
        - subject and/or body (at least one required)
        - sender (optional)

    Returns:
        A DataFrame with the normalized columns in OUTPUT_FIELDS order.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        DatasetValidationError: If the file, schema, or any record is invalid.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    if not file_path.is_file():
        raise DatasetValidationError(
            f"Dataset path is not a file: {file_path}"
        )

    if file_path.stat().st_size == 0:
        raise DatasetValidationError("Dataset file is empty.")

    # Check the original header so duplicate column names aren't overlooked.
    try:
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader, None)
    except UnicodeDecodeError as exc:
        raise DatasetValidationError(
            "Dataset must be a valid UTF-8 CSV file."
        ) from exc
    except csv.Error as exc:
        raise DatasetValidationError(
            f"Could not read the CSV header: {exc}"
        ) from exc

    if not headers or not any(name.strip() for name in headers):
        raise DatasetValidationError("Dataset has no usable header.")

    headers = [name.strip() for name in headers]

    if len(headers) != len(set(headers)):
        raise DatasetValidationError(
            "Dataset contains duplicate column names."
        )

    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except pd.errors.EmptyDataError as exc:
        raise DatasetValidationError("Dataset CSV is empty.") from exc
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise DatasetValidationError(
            f"Dataset CSV could not be read: {exc}"
        ) from exc

    df.columns = [str(column).strip() for column in df.columns]

    if df.empty:
        raise DatasetValidationError(
            "Dataset contains a header but no data rows."
        )

    if "label" not in df.columns:
        raise DatasetValidationError(
            "Missing required column: 'label'."
        )

    if not {"subject", "body"} & set(df.columns):
        raise DatasetValidationError(
            "Dataset must contain at least one of 'subject' or 'body'."
        )

    # Sender is optional. Missing subject/body values are allowed individually,
    # but the existing preprocessing function requires at least one to be
    # non-empty for each email.
    for column in OUTPUT_FIELDS:
        if column not in df.columns:
            df[column] = None

    records = []
    for row in df[list(OUTPUT_FIELDS)].to_dict(orient="records"):
        record = {}
        for field, value in row.items():
            # Convert pandas missing values (NaN/NA) to None. This allows the
            # existing preprocessing code to handle missing fields correctly.
            record[field] = None if pd.isna(value) else value
        records.append(record)

    result = preprocess_emails(records)

    if result.errors:
        details = "; ".join(
            f"row {error.index + 2}: {error.message}"
            for error in result.errors[:5]
        )
        extra = (
            f" ({len(result.errors) - 5} more invalid row(s))"
            if len(result.errors) > 5
            else ""
        )
        raise DatasetValidationError(
            f"Dataset contains {len(result.errors)} invalid record(s): "
            f"{details}{extra}"
        )

    return pd.DataFrame(result.valid, columns=OUTPUT_FIELDS)
