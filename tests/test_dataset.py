"""Tests for src/dataset.py."""

import json
from pathlib import Path

import pytest

from src import dataset as ds

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def valid_config_dict(**overrides):
    config = {
        "path": "emails.csv",
        "columns": {"subject": "Subject", "body": "Body", "sender": "Sender", "label": "Label"},
    }
    config.update(overrides)
    return config


# --------------------------------------------------------------------------
# Config validation
# --------------------------------------------------------------------------


def test_parse_config_accepts_minimal_valid_config():
    config = ds.parse_config(valid_config_dict())

    assert config.path == "emails.csv"
    assert config.columns["label"] == "Label"
    assert config.label_map == {}
    assert config.delimiter == ","
    assert config.max_rows is None


def test_parse_config_accepts_label_and_body_only():
    config = ds.parse_config({"path": "x.csv", "columns": {"body": "text", "label": "y"}})

    assert set(config.columns) == {"body", "label"}


@pytest.mark.parametrize(
    "data, message",
    [
        ("not a dict", "must be a JSON object"),
        ({"columns": {"body": "b", "label": "l"}}, "'path' must be a non-empty string"),
        ({"path": "  ", "columns": {"body": "b", "label": "l"}}, "'path' must be a non-empty string"),
        ({"path": "x.csv"}, "'columns' must be an object"),
        ({"path": "x.csv", "columns": {"body": "b"}}, "must include 'label'"),
        ({"path": "x.csv", "columns": {"sender": "s", "label": "l"}}, "at least one of 'subject' or 'body'"),
        ({"path": "x.csv", "columns": {"body": "b", "label": "l", "color": "c"}}, "Unknown fields in 'columns'"),
        ({"path": "x.csv", "columns": {"body": "", "label": "l"}}, "non-empty string"),
        (valid_config_dict(extra=1), "Unknown config keys"),
        (valid_config_dict(label_map={"Spam": "spam"}), "must be one of"),
        (valid_config_dict(label_map=["a"]), "'label_map' must be an object"),
        (valid_config_dict(delimiter=";;"), "single character"),
        (valid_config_dict(encoding="no-such-encoding"), "Unknown encoding"),
        (valid_config_dict(max_rows=0), "positive integer"),
        (valid_config_dict(max_rows=True), "positive integer"),
        (valid_config_dict(max_rows="10"), "positive integer"),
    ],
)
def test_parse_config_rejects_invalid_configs(data, message):
    with pytest.raises(ds.DatasetError, match=message):
        ds.parse_config(data)


def test_load_config_reads_json_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(valid_config_dict(max_rows=5)), encoding="utf-8")

    config = ds.load_config(path)

    assert config.max_rows == 5


def test_load_config_reports_missing_file_and_bad_json(tmp_path):
    with pytest.raises(ds.DatasetError, match="Config file not found"):
        ds.load_config(tmp_path / "missing.json")

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ds.DatasetError, match="not valid JSON"):
        ds.load_config(bad)


def test_example_config_in_repo_is_valid():
    config = ds.load_config(PROJECT_ROOT / "configs" / "dataset.example.json")

    assert config.columns["label"] == "Label"
    assert config.label_map["Phishing Email"] == "phishing"

def test_load_dataset_reads_and_preprocesses_csv(tmp_path):
    csv_path = tmp_path / "emails.csv"
    csv_path.write_text(
        "Subject,Body,Sender,Label\n"
        '" Urgent offer "," Click here ","sender@example.com",Phishing Email\n'
        '"Meeting","See you tomorrow","colleague@example.com",Legitimate Email\n',
        encoding="utf-8",
    )

    config = ds.DatasetConfig(
        path=str(csv_path),
        columns={
            "subject": "Subject",
            "body": "Body",
            "sender": "Sender",
            "label": "Label",
        },
        label_map={
            "Phishing Email": "phishing",
            "Legitimate Email": "legitimate",
        },
    )

    result = ds.load_dataset(config)

    assert result.errors == []
    assert len(result.valid) == 2
    assert result.valid[0]["subject"] == "Urgent offer"
    assert result.valid[0]["label"] == "phishing"
    assert result.valid[1]["label"] == "legitimate"


def test_load_dataset_rejects_missing_configured_columns(tmp_path):
    csv_path = tmp_path / "emails.csv"
    csv_path.write_text("Subject,Label\nHello,phishing\n", encoding="utf-8")

    config = ds.DatasetConfig(
        path=str(csv_path),
        columns={"subject": "Subject", "body": "Body", "label": "Label"},
    )

    with pytest.raises(ds.DatasetError, match="missing configured columns"):
        ds.load_dataset(config)


def test_load_dataset_rejects_empty_csv(tmp_path):
    csv_path = tmp_path / "emails.csv"
    csv_path.write_text("Subject,Body,Label\n", encoding="utf-8")

    config = ds.DatasetConfig(
        path=str(csv_path),
        columns={"subject": "Subject", "body": "Body", "label": "Label"},
    )

    with pytest.raises(ds.DatasetError, match="no data rows"):
        ds.load_dataset(config)


def test_load_dataset_applies_max_rows(tmp_path):
    csv_path = tmp_path / "emails.csv"
    csv_path.write_text(
        "Subject,Body,Label\n"
        "First,First body,phishing\n"
        "Second,Second body,legitimate\n",
        encoding="utf-8",
    )

    config = ds.DatasetConfig(
        path=str(csv_path),
        columns={"subject": "Subject", "body": "Body", "label": "Label"},
        max_rows=1,
    )

    result = ds.load_dataset(config)

    assert len(result.valid) == 1
    assert result.valid[0]["subject"] == "First"