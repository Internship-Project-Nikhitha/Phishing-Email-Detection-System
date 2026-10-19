
"""Tests for CSV dataset loading and schema validation."""

import pandas as pd
import pytest

from src.dataset import DatasetValidationError, load_dataset


def write_csv(tmp_path, name, rows, columns=None):
    path = tmp_path / name
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
    return path


def test_load_valid_dataset(tmp_path):
    path = write_csv(
        tmp_path,
        "emails.csv",
        {
            "subject": ["Account alert", "Class tomorrow"],
            "body": ["Verify your account", "Lecture starts at 10"],
            "sender": ["unknown@example.test", "teacher@example.test"],
            "label": ["Phishing", "safe_email"],
        },
    )

    result = load_dataset(path)

    assert list(result.columns) == [
        "subject", "body", "sender", "label"
    ]
    assert len(result) == 2
    assert result["label"].tolist() == ["phishing", "legitimate"]
    assert result.iloc[0]["subject"] == "Account alert"


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "missing.csv")


def test_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(DatasetValidationError, match="empty"):
        load_dataset(path)


def test_header_without_rows(tmp_path):
    path = tmp_path / "no_rows.csv"
    path.write_text("subject,body,label\n", encoding="utf-8")

    with pytest.raises(DatasetValidationError, match="no data rows"):
        load_dataset(path)


def test_missing_label_column(tmp_path):
    path = write_csv(
        tmp_path,
        "no_label.csv",
        {"subject": ["Hello"], "body": ["Test message"]},
    )

    with pytest.raises(DatasetValidationError, match="label"):
        load_dataset(path)


def test_missing_subject_and_body_columns(tmp_path):
    path = write_csv(
        tmp_path,
        "wrong_columns.csv",
        {"message": ["Hello"], "label": ["phishing"]},
    )

    with pytest.raises(DatasetValidationError, match="subject.*body"):
        load_dataset(path)


def test_blank_email_is_rejected(tmp_path):
    path = write_csv(
        tmp_path,
        "blank_email.csv",
        {"subject": ["  "], "body": [None], "label": ["phishing"]},
    )

    with pytest.raises(DatasetValidationError, match="no usable content"):
        load_dataset(path)


def test_unknown_label_is_rejected(tmp_path):
    path = write_csv(
        tmp_path,
        "unknown_label.csv",
        {"subject": ["Example"], "label": ["spam"]},
    )

    with pytest.raises(DatasetValidationError, match="Unknown label"):
        load_dataset(path)


def test_missing_sender_is_allowed(tmp_path):
    path = write_csv(
        tmp_path,
        "no_sender.csv",
        {"body": ["This is an email"], "label": ["legitimate"]},
    )

    result = load_dataset(path)

    assert result.iloc[0]["sender"] == ""
    assert result.iloc[0]["label"] == "legitimate"


def test_duplicate_column_names_are_rejected(tmp_path):
    path = tmp_path / "duplicate_columns.csv"
    path.write_text(
        "subject,subject,label\nHello,World,phishing\n",
        encoding="utf-8",
    )

    with pytest.raises(DatasetValidationError, match="duplicate column"):
        load_dataset(path)


def test_missing_label_value_is_rejected(tmp_path):
    path = write_csv(
        tmp_path,
        "missing_label_value.csv",
        {"subject": ["Example"], "label": [None]},
    )

    with pytest.raises(DatasetValidationError, match="Label is missing"):
        load_dataset(path)


def test_preprocessing_normalizes_whitespace(tmp_path):
    path = write_csv(
        tmp_path,
        "whitespace.csv",
        {
            "subject": ["  Urgent   account  "],
            "body": ["Please\n verify\t now"],
            "label": ["phishing"],
        },
    )

    result = load_dataset(path)

    assert result.iloc[0]["subject"] == "Urgent account"
    assert result.iloc[0]["body"] == "Please verify now"
