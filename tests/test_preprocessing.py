"""Tests for src/preprocessing.py (Day 1)."""

import socket
import sys
import urllib.request
from pathlib import Path

import pytest

# Make `src` importable even when running plain `pytest` from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing import (  # noqa: E402
    BatchResult,
    EmailValidationError,
    RecordError,
    normalize_label,
    normalize_text,
    preprocess_email,
    preprocess_emails,
)


# --------------------------------------------------------------------------
# Valid records
# --------------------------------------------------------------------------


def test_valid_phishing_email():
    record = {
        "subject": "Urgent: verify your account",
        "body": "Your account is locked. Log in to restore access.",
        "sender": "support@bank-alerts.example.invalid",
        "label": "Phishing",
    }

    result = preprocess_email(record)

    assert result == {
        "subject": "Urgent: verify your account",
        "body": "Your account is locked. Log in to restore access.",
        "sender": "support@bank-alerts.example.invalid",
        "label": "phishing",
    }


def test_valid_legitimate_email():
    record = {
        "subject": "Team meeting moved to 3pm",
        "body": "Hi all, the weekly meeting is now at 3pm in room 4.",
        "sender": "team@example.com",
        "label": "legitimate",
    }

    result = preprocess_email(record)

    assert result == {
        "subject": "Team meeting moved to 3pm",
        "body": "Hi all, the weekly meeting is now at 3pm in room 4.",
        "sender": "team@example.com",
        "label": "legitimate",
    }


def test_output_has_exactly_the_documented_fields_and_ignores_extra_keys():
    record = {
        "subject": "Hello",
        "body": "World",
        "sender": "a@example.com",
        "label": "legitimate",
        "id": 123,
        "notes": "should be ignored",
    }

    result = preprocess_email(record)

    assert set(result) == {"subject", "body", "sender", "label"}
    assert all(isinstance(value, str) for value in result.values())


def test_preprocess_email_does_not_modify_the_input_record():
    record = {"subject": "  Hi   there ", "body": None, "label": " PHISH "}
    snapshot = dict(record)

    preprocess_email(record)

    assert record == snapshot


# --------------------------------------------------------------------------
# Label normalization
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("phishing", "phishing"),
        ("PHISHING", "phishing"),
        ("  Phishing  ", "phishing"),
        ("phishing_email", "phishing"),
        ("Phishing-Email", "phishing"),
        ("phish", "phishing"),
        ("malicious", "phishing"),
        ("1", "phishing"),
        (1, "phishing"),
        ("legitimate", "legitimate"),
        ("Legitimate", "legitimate"),
        ("LEGIT", "legitimate"),
        ("ham", "legitimate"),
        ("Safe Email", "legitimate"),
        ("safe_email", "legitimate"),
        ("benign", "legitimate"),
        ("0", "legitimate"),
        (0, "legitimate"),
    ],
)
def test_normalize_label_recognized_variants(raw, expected):
    assert normalize_label(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["spam", "suspicious", "not phishing", "2", 2, -1, "-1", "-0", "_phishing", "phishing-", "_-_"],
)
def test_normalize_label_rejects_unknown_labels(raw):
    with pytest.raises(EmailValidationError, match="Unknown label"):
        normalize_label(raw)


@pytest.mark.parametrize("raw", [True, False, 1.0, ["phishing"], {"label": "phishing"}])
def test_normalize_label_rejects_unsupported_types(raw):
    with pytest.raises(EmailValidationError, match="must be a string or an integer"):
        normalize_label(raw)


def test_normalize_label_rejects_none_as_missing():
    with pytest.raises(EmailValidationError, match="missing"):
        normalize_label(None)


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_normalize_label_rejects_empty_labels(raw):
    with pytest.raises(EmailValidationError, match="empty"):
        normalize_label(raw)


# --------------------------------------------------------------------------
# Missing optional fields
# --------------------------------------------------------------------------


def test_missing_subject_and_sender_default_to_empty_strings():
    result = preprocess_email({"body": "Meeting at 3pm.", "label": "legitimate"})

    assert result == {
        "subject": "",
        "body": "Meeting at 3pm.",
        "sender": "",
        "label": "legitimate",
    }


def test_missing_body_is_allowed_when_subject_has_text():
    result = preprocess_email({"subject": "Free prize!!!", "label": "phishing"})

    assert result["subject"] == "Free prize!!!"
    assert result["body"] == ""
    assert result["sender"] == ""


def test_none_values_for_optional_fields_are_treated_as_missing():
    record = {"subject": None, "body": "Hello", "sender": None, "label": "ham"}

    result = preprocess_email(record)

    assert result["subject"] == ""
    assert result["sender"] == ""
    assert result["body"] == "Hello"


# --------------------------------------------------------------------------
# Missing or invalid labels (record level)
# --------------------------------------------------------------------------


def test_record_without_label_key_is_rejected():
    with pytest.raises(EmailValidationError, match="Label is missing"):
        preprocess_email({"subject": "Hi", "body": "There"})


@pytest.mark.parametrize("label", [None, "", "   "])
def test_record_with_none_or_blank_label_is_rejected(label):
    with pytest.raises(EmailValidationError, match="Label is (missing|empty)"):
        preprocess_email({"subject": "Hi", "body": "There", "label": label})


def test_record_with_unknown_label_is_rejected():
    with pytest.raises(EmailValidationError, match="Unknown label 'spam'"):
        preprocess_email({"subject": "Hi", "body": "There", "label": "spam"})


# --------------------------------------------------------------------------
# Empty or unusable content
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "record",
    [
        {"label": "phishing"},
        {"subject": "", "body": "", "label": "phishing"},
        {"subject": "   ", "body": "\n\t  ", "label": "phishing"},
        {"subject": None, "body": None, "label": "phishing"},
        {"sender": "someone@example.com", "label": "phishing"},
    ],
)
def test_record_without_subject_or_body_text_is_rejected(record):
    with pytest.raises(EmailValidationError, match="no usable content"):
        preprocess_email(record)


@pytest.mark.parametrize(
    "field_name, bad_value",
    [("subject", 42), ("body", ["a", "b"]), ("sender", {"x": 1}), ("body", 3.5)],
)
def test_non_string_text_fields_are_rejected_with_field_name(field_name, bad_value):
    record = {"subject": "Hi", "body": "There", "sender": "a@example.com", "label": "ham"}
    record[field_name] = bad_value

    with pytest.raises(EmailValidationError, match=f"'{field_name}' must be a string"):
        preprocess_email(record)


# --------------------------------------------------------------------------
# Invalid input types
# --------------------------------------------------------------------------


@pytest.mark.parametrize("bad_input", [None, "just a string", 42, 3.5, ["a"], ("a",)])
def test_preprocess_email_rejects_non_dict_input(bad_input):
    with pytest.raises(EmailValidationError, match="must be a dict"):
        preprocess_email(bad_input)


@pytest.mark.parametrize(
    "bad_input",
    [
        "just a string",
        None,
        5,
        {"subject": "Hi", "body": "There", "label": "ham"},
        (record for record in []),
    ],
)
def test_preprocess_emails_rejects_non_list_input(bad_input):
    with pytest.raises(EmailValidationError, match="list or tuple"):
        preprocess_emails(bad_input)


def test_preprocess_emails_suggests_single_record_function_for_a_dict():
    with pytest.raises(EmailValidationError, match="preprocess_email"):
        preprocess_emails({"subject": "Hi", "body": "There", "label": "ham"})


def test_normalize_text_rejects_non_string_input():
    with pytest.raises(EmailValidationError, match="must be a string"):
        normalize_text(123)


# --------------------------------------------------------------------------
# Whitespace normalization
# --------------------------------------------------------------------------


def test_normalize_text_collapses_spaces_tabs_and_newlines():
    assert normalize_text("  Hello \n\n  world\t!  ") == "Hello world !"


def test_normalize_text_handles_unicode_whitespace():
    assert normalize_text("a  b c") == "a b c"


def test_normalize_text_keeps_punctuation_intact():
    text = "Hi,   it's   (urgent)!!!  Cost: $5.00; ok?  [see below]"

    assert normalize_text(text) == "Hi, it's (urgent)!!! Cost: $5.00; ok? [see below]"


@pytest.mark.parametrize("text", ["", "   ", "\n\t\r\n"])
def test_normalize_text_returns_empty_string_for_blank_input(text):
    assert normalize_text(text) == ""


def test_preprocess_email_normalizes_whitespace_in_all_text_fields():
    record = {
        "subject": "  Account \n alert  ",
        "body": "Dear   user,\n\nPlease   act\tnow.  ",
        "sender": "  Alice Example   <alice@example.com>  ",
        "label": "phishing",
    }

    result = preprocess_email(record)

    assert result["subject"] == "Account alert"
    assert result["body"] == "Dear user, Please act now."
    assert result["sender"] == "Alice Example <alice@example.com>"


# --------------------------------------------------------------------------
# URL preservation (and no network access)
# --------------------------------------------------------------------------

SUSPICIOUS_URLS = [
    "http://paypa1-secure.example.invalid/login?user=1&token=abc%20def",
    "HTTPS://Evil.Example.INVALID/Path/CaSe?x=1#frag",
    "hxxp://obfuscated[.]example[.]invalid/a_b-c",
    "http://192.0.2.1:8080/verify.php?id=42",
]


@pytest.mark.parametrize("url", SUSPICIOUS_URLS)
def test_urls_are_preserved_exactly_and_never_accessed(monkeypatch, url):
    network_calls = []

    def forbidden(*args, **kwargs):
        network_calls.append(args)
        raise AssertionError("Network access attempted during preprocessing.")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)

    record = {
        "subject": f"Check   {url}",
        "body": f"Please\n visit {url}   now.",
        "sender": "alerts@example.invalid",
        "label": "phishing",
    }

    result = preprocess_email(record)

    assert result["subject"] == f"Check {url}"
    assert result["body"] == f"Please visit {url} now."
    assert network_calls == []


# --------------------------------------------------------------------------
# Batch processing
# --------------------------------------------------------------------------


def test_preprocess_emails_all_valid():
    records = [
        {"subject": "Win a prize", "body": "Click here", "label": "phish"},
        {"subject": "Lunch?", "body": "Noon works for me.", "label": "ham"},
    ]

    result = preprocess_emails(records)

    assert isinstance(result, BatchResult)
    assert result.errors == []
    assert [email["label"] for email in result.valid] == ["phishing", "legitimate"]
    assert [email["subject"] for email in result.valid] == ["Win a prize", "Lunch?"]


def test_preprocess_emails_mixed_valid_and_invalid_records():
    records = [
        {"subject": "Verify now", "body": "Click the link", "label": "phishing"},  # 0 ok
        {"subject": "Hello", "body": "World", "label": "spam"},  # 1 bad label
        "not a dict",  # 2 wrong type
        {"subject": "Report", "body": "Attached.", "label": "legitimate"},  # 3 ok
        {"subject": "", "body": "", "label": "phishing"},  # 4 no content
    ]

    result = preprocess_emails(records)

    assert [email["subject"] for email in result.valid] == ["Verify now", "Report"]
    assert [error.index for error in result.errors] == [1, 2, 4]
    assert all(isinstance(error, RecordError) for error in result.errors)
    assert "Unknown label" in result.errors[0].message
    assert "must be a dict" in result.errors[1].message
    assert "no usable content" in result.errors[2].message


def test_preprocess_emails_accepts_tuple_and_empty_input():
    record = {"subject": "Hi", "body": "There", "label": "0"}

    from_tuple = preprocess_emails((record,))
    from_empty = preprocess_emails([])

    assert len(from_tuple.valid) == 1
    assert from_tuple.errors == []
    assert from_empty.valid == []
    assert from_empty.errors == []
