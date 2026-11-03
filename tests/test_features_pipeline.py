"""Tests for src/features/pipeline.py."""

import pytest

from src.features import pipeline as fp

RECORD = {
    "subject": "URGENT: verify your account!",
    "body": 'Log in at <a href="http://evil.example.invalid/x">www.mybank.example.com</a> now',
    "sender": "paypal.com <help@bad-site.example.top>",
    "label": "phishing",
}


def test_extract_all_returns_every_feature_in_fixed_order():
    result = fp.extract_all(RECORD)

    assert list(result) == fp.feature_names()
    assert all(isinstance(value, float) for value in result.values())


def test_feature_names_come_from_all_three_modules():
    names = fp.feature_names()

    assert any(name.startswith("sender_") for name in names)
    assert any(name.startswith("url_") for name in names)
    assert any(name.startswith("text_") for name in names)
    assert len(set(names)) == len(names)


def test_empty_record_gives_a_complete_all_zero_vector():
    result = fp.extract_all({})

    assert list(result) == fp.feature_names()
    assert set(result.values()) == {0.0}


def test_descriptions_cover_every_feature():
    descriptions = fp.feature_descriptions()

    assert set(descriptions) == set(fp.feature_names())
    assert all(text.strip() for text in descriptions.values())


def test_extract_all_rejects_non_dict_records():
    with pytest.raises(TypeError):
        fp.extract_all("not a dict")


# @@PART 2
def test_the_example_phishing_record_triggers_expected_features():
    result = fp.extract_all(RECORD)

    assert result["sender_display_name_mismatch"] == 1.0
    assert result["sender_suspicious_tld"] == 1.0
    assert result["url_anchor_mismatch"] == 1.0
    assert result["url_plain_http"] == 1.0
    assert result["text_urgent_words"] >= 1.0
    assert result["text_credential_words"] >= 1.0


def test_extract_many_keeps_order_and_handles_empty_lists():
    records = [RECORD, {"subject": "Lunch", "body": "Noon?", "sender": "a@example.com"}]

    result = fp.extract_many(records)

    assert len(result) == 2
    assert result[0]["sender_suspicious_tld"] == 1.0
    assert result[1]["sender_suspicious_tld"] == 0.0
    assert fp.extract_many([]) == []


def test_check_pipeline_reports_no_problems():
    assert fp.check_pipeline() == []


def test_features_are_deterministic():
    assert fp.extract_all(RECORD) == fp.extract_all(dict(RECORD))
