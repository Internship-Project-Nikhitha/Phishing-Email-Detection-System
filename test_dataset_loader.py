import pandas as pd
import pytest

from src.data.dataset_loader import DatasetLoadError, load_dataset
from src.data.validate_dataset import audit_dataset


LABELS = {"1": "phishing", "0": "legitimate", "phishing": "phishing", "ham": "legitimate"}


def write_csv(tmp_path, text):
    path = tmp_path / "emails.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_and_normalizes_explicit_labels(tmp_path):
    path = write_csv(tmp_path, "body,class\n'Click https://x.test', PHISHING \nHello,ham\n")
    result = load_dataset(
        path,
        column_mapping={"text": "body", "label": "class"},
        label_mapping={" phishing ": "phishing", "ham": "legitimate"},
    )
    assert result.dataframe["label"].tolist() == ["phishing", "legitimate"]
    assert result.dataframe["source_label"].tolist() == [" PHISHING ", "ham"]
    assert result.summary["label_distribution"] == {"phishing": 1, "legitimate": 1}


def test_missing_columns_are_clear_error(tmp_path):
    path = write_csv(tmp_path, "wrong,text\nx,hello\n")
    with pytest.raises(DatasetLoadError, match="Required source column"):
        load_dataset(path, label_mapping={"yes": "phishing"})


def test_missing_empty_text_and_unknown_labels_report_without_content(tmp_path):
    path = write_csv(tmp_path, "text,label\n,ham\nhello,other\n   ,phishing\n")
    result = load_dataset(path, label_mapping={"phishing": "phishing", "ham": "legitimate"})
    assert result.dataframe.empty
    assert result.summary["missing_or_empty_text_rows"] == 2
    assert result.summary["unknown_or_missing_label_rows"] == 1
    assert "text" not in result.invalid_rows.columns


def test_removes_exact_duplicates_and_reports_count(tmp_path):
    path = write_csv(tmp_path, "text,label\nhello,ham\nhello,ham\nalert,phishing\n")
    result = load_dataset(path, label_mapping={"phishing": "phishing", "ham": "legitimate"})
    assert len(result.dataframe) == 2
    assert result.summary["exact_duplicate_rows"] == 1
    assert result.summary["duplicates_removed"] == 1


def test_conflicting_duplicate_labels_are_invalid(tmp_path):
    path = write_csv(tmp_path, "text,label\nhello,ham\nhello,phishing\n")
    result = load_dataset(path, label_mapping={"phishing": "phishing", "ham": "legitimate"})
    assert result.dataframe.empty
    assert result.summary["conflicting_duplicate_rows"] == 2


def test_bad_path_unsupported_format_and_missing_label_map(tmp_path):
    with pytest.raises(DatasetLoadError, match="does not exist"):
        load_dataset(tmp_path / "missing.csv", label_mapping=LABELS)
    other = tmp_path / "emails.xlsx"
    other.write_text("untrusted data", encoding="utf-8")
    with pytest.raises(DatasetLoadError, match="Unsupported dataset format"):
        load_dataset(other, label_mapping=LABELS)
    path = write_csv(tmp_path, "text,label\na,b\n")
    with pytest.raises(DatasetLoadError, match="explicit label_mapping"):
        load_dataset(path, label_mapping={})


def test_jsonl_supported(tmp_path):
    path = tmp_path / "emails.jsonl"
    path.write_text('{"body":"look here","kind":1}\n', encoding="utf-8")
    result = load_dataset(
        path,
        column_mapping={"text": "body", "label": "kind"},
        label_mapping={"1": "phishing"},
    )
    assert result.dataframe.loc[0, "label"] == "phishing"


def test_malformed_json_values_are_reported_without_exposing_content(tmp_path):
    path = tmp_path / "emails.jsonl"
    path.write_text(
        '{"text": {"private": "payload"}, "label": ["phishing"]}\n'
        '{"text": "valid body", "label": "phishing"}\n',
        encoding="utf-8",
    )
    result = load_dataset(path, label_mapping={"phishing": "phishing"})
    assert result.dataframe["text"].tolist() == ["valid body"]
    assert result.summary["malformed_text_rows"] == 1
    assert result.summary["unknown_or_missing_label_rows"] == 1
    assert result.invalid_rows["source_row"].tolist() == [1, 1]
    assert "private" not in result.invalid_rows.to_json()


def test_audit_detects_sensitive_indicators_html_and_split_leakage():
    train = pd.DataFrame({"text": ["from a@example.test <b>hello</b>", "same"]})
    test = pd.DataFrame(
        {"text": ["same https://bad.test", "same"], "campaign": ["c2", "c3"]}
    )
    train["campaign"] = ["c1", "c1"]
    report = audit_dataset(
        pd.DataFrame(
            {"text": [train.loc[0, "text"], "same https://bad.test"], "label": ["legitimate", "phishing"]}
        ),
        train=train,
        test=test,
        group_column="campaign",
    )
    assert report["email_address_rows"] == 1
    assert report["url_rows"] == 1
    assert report["html_rows"] == 1
    assert report["train_test_exact_duplicate_texts"] == 1
    assert report["group_overlap_count"] == 0
    assert report["class_imbalance_ratio"] == 1.0


def test_audit_counts_ip_and_phone_like_indicators():
    report = audit_dataset(
        pd.DataFrame(
            {
                "text": ["contact 555-010-2345 from 192.0.2.10", "plain message"],
                "label": ["phishing", "legitimate"],
            }
        )
    )
    assert report["ipv4_address_rows"] == 1
    assert report["phone_like_rows"] == 1