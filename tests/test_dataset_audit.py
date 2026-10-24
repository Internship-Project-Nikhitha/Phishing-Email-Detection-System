"""Tests for privacy-conscious dataset audit reporting."""

import json

import pytest

from src.audit_dataset import main
from src.quality import audit_dataset


def make_record(subject, body, label="legitimate", sender=""):
    return {"subject": subject, "body": body, "label": label, "sender": sender}


def test_audit_reports_counts_without_returning_email_content():
    private_text = (
        "Contact person@example.com at https://example.invalid/login "
        "or 192.168.1.10, call +1 212-555-0123 <p>HTML</p>"
    )
    report = audit_dataset(
        [
            make_record("Alert", private_text, "phishing"),
            make_record("Alert", private_text, "phishing"),
            make_record("", "", "unknown"),
        ]
    )

    assert report["rows"] == 3
    assert report["empty_text_rows"] == 1
    assert report["exact_duplicate_text_rows"] == 1
    assert report["invalid_label_rows"] == 1
    assert report["label_distribution"] == {"phishing": 2, "legitimate": 0}
    assert report["class_imbalance_ratio"] is None
    assert report["email_address_rows"] == 2
    assert report["url_rows"] == 2
    assert report["ipv4_address_rows"] == 2
    assert report["phone_like_rows"] == 2
    assert report["html_rows"] == 2
    assert private_text not in json.dumps(report)


def test_audit_reports_class_balance_and_split_leakage():
    phishing = make_record("Suspicious", "Verify now", "phishing")
    legitimate = make_record("Meeting", "See you", "legitimate")
    report = audit_dataset(
        [phishing, legitimate],
        train=[{**phishing, "source": "corpus-a"}, {**legitimate, "source": "corpus-a"}],
        test=[{**phishing, "source": "corpus-b"}],
        group_field="source",
    )

    assert report["class_imbalance_ratio"] == 1.0
    assert report["train_test_exact_duplicate_emails"] == 1
    assert report["group_overlap_count"] == 0


def test_audit_reports_overlapping_groups_and_imbalanced_classes():
    train = [
        make_record("Phish one", "Body one", "phishing", sender="shared@example.invalid"),
        make_record("Legitimate", "Body three", "legitimate"),
    ]
    test = [
        make_record("Other", "Body four", "legitimate", sender="shared@example.invalid")
    ]

    report = audit_dataset(
        train + test,
        train=train,
        test=test,
        group_field="sender",
    )

    assert report["class_imbalance_ratio"] == 2.0
    assert report["group_overlap_count"] == 1
    assert report["train_test_exact_duplicate_emails"] == 0


def test_audit_empty_records_returns_zero_counts():
    report = audit_dataset([])

    assert report["rows"] == 0
    assert report["empty_text_rows"] == 0
    assert report["exact_duplicate_text_rows"] == 0
    assert report["invalid_label_rows"] == 0
    assert report["label_distribution"] == {"phishing": 0, "legitimate": 0}
    assert report["class_imbalance_ratio"] is None


def test_audit_rejects_invalid_options_and_records():
    record = make_record("Subject", "Body")

    with pytest.raises(ValueError, match="both be provided"):
        audit_dataset([record], train=[record])
    with pytest.raises(ValueError, match="requires both"):
        audit_dataset([record], group_field="source")
    with pytest.raises(ValueError, match="must exist in every record"):
        audit_dataset(
            [record],
            train=[record],
            test=[record],
            group_field="source",
        )
    with pytest.raises(TypeError, match="must be a list"):
        audit_dataset((record,))
    with pytest.raises(TypeError, match="must be a string"):
        audit_dataset([make_record("Subject", 42)])


def test_audit_cli_loads_config_and_prints_no_email_content(tmp_path, capsys):
    email_content = "private body text unique marker"
    (tmp_path / "emails.csv").write_text(
        "Body,Label\n"
        f"{email_content},phishing\n"
        "Ordinary correspondence,legitimate\n",
        encoding="utf-8",
    )
    config = {
        "path": "emails.csv",
        "columns": {"body": "Body", "label": "Label"},
    }
    config_path = tmp_path / "dataset.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    main([str(config_path)])

    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["rows"] == 2
    assert report["invalid_record_count"] == 0
    assert email_content not in output
