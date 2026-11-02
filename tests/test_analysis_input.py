"""Tests for src/analysis_input.py."""

import pytest

from src.analysis_input import prepare_for_analysis
from src.preprocessing import EmailValidationError


def test_cleans_whitespace_and_fills_missing_fields():
    result = prepare_for_analysis({"subject": "  Hi \n there ", "body": None})

    assert result == {"subject": "Hi there", "body": "", "sender": ""}


def test_no_label_is_needed_and_extra_keys_are_ignored():
    result = prepare_for_analysis({"body": "Hello", "label": "phishing", "id": 7})

    assert set(result) == {"subject", "body", "sender"}


def test_urls_are_kept_exactly_as_text():
    url = "http://evil.example.invalid/Login?x=1&y=%20z"

    assert prepare_for_analysis({"body": f"Go   to {url}  now"})["body"] == f"Go to {url} now"


@pytest.mark.parametrize("bad", [None, "text", 5, ["a"]])
def test_non_dict_input_is_rejected(bad):
    with pytest.raises(EmailValidationError, match="must be a dict"):
        prepare_for_analysis(bad)


def test_empty_content_and_wrong_types_are_rejected():
    with pytest.raises(EmailValidationError, match="no usable content"):
        prepare_for_analysis({"sender": "a@example.com"})
    with pytest.raises(EmailValidationError, match="no usable content"):
        prepare_for_analysis({"subject": "  ", "body": "\n"})
    with pytest.raises(EmailValidationError, match="'body' must be a string"):
        prepare_for_analysis({"subject": "x", "body": 12})


def test_input_is_not_modified():
    record = {"subject": " a ", "body": "b"}
    snapshot = dict(record)

    prepare_for_analysis(record)

    assert record == snapshot
