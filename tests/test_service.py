"""Tests for src/service.py (uses a fake predictor, so no scikit-learn is needed)."""

import pytest

from src import service, storage
from src.preprocessing import EmailValidationError
from tests.helpers import FakePredictor

PHISHY = {
    "subject": "Verify your password",
    "body": 'Log in at <a href="http://evil.example.invalid/x">www.mybank.example.com</a> now!',
    "sender": "paypal.com <help@bad.example.top>",
}
NORMAL = {"subject": "Lunch", "body": "Noon at the cafe?", "sender": "a@example.com"}


def test_analyze_record_returns_the_documented_fields():
    result = service.analyze_record(PHISHY, FakePredictor())

    assert set(result) == {"score", "label", "risk_level", "indicators", "model_version", "content_sha256", "warnings"}
    assert result["label"] == "phishing"
    assert result["risk_level"] == "high"
    assert result["model_version"] == "fake-1"
    assert len(result["content_sha256"]) == 64
    assert result["indicators"][0]["feature"] == "word:password"


def test_legitimate_email_gets_a_low_score_and_label():
    result = service.analyze_record(NORMAL, FakePredictor())

    assert (result["label"], result["risk_level"]) == ("legitimate", "low")


def test_indicators_include_feature_values_from_the_real_feature_pipeline():
    result = service.analyze_record(PHISHY, FakePredictor(contributions={"url_anchor_mismatch": 0.7}))

    indicator = result["indicators"][0]
    assert indicator["feature"] == "url_anchor_mismatch"
    assert indicator["value"] == 1.0
    assert "different domain" in indicator["description"]


def test_custom_thresholds_and_extra_warnings_are_applied():
    result = service.analyze_record(
        NORMAL,
        FakePredictor(score=0.5),
        thresholds={"medium": 0.6, "high": 0.9},
        decision_threshold=0.45,
        extra_warnings=["Attachment 'x.exe' looks executable."],
    )

    assert result["risk_level"] == "low"
    assert result["label"] == "phishing"
    assert result["warnings"] == ["Attachment 'x.exe' looks executable."]


def test_invalid_email_and_invalid_predictor_scores_raise_clear_errors():
    with pytest.raises(EmailValidationError, match="no usable content"):
        service.analyze_record({"subject": "", "body": ""}, FakePredictor())
    with pytest.raises(ValueError, match="invalid score"):
        service.analyze_record(NORMAL, FakePredictor(score=1.5))


def test_content_hash_is_the_same_for_the_same_email_regardless_of_spacing():
    first = service.analyze_record({"subject": "Hi", "body": "There"}, FakePredictor())
    second = service.analyze_record({"subject": " hi ", "body": "There  "}, FakePredictor())

    assert first["content_sha256"] == second["content_sha256"]


# @@PART 2
@pytest.fixture
def conn():
    connection = storage.connect(":memory:")
    yield connection
    connection.close()


def test_analyze_and_store_saves_a_row_and_returns_its_id(conn):
    result = service.analyze_and_store(conn, PHISHY, FakePredictor(), source_name="mail.eml")

    assert result["id"] == 1
    stored = storage.get_analysis(conn, 1)
    assert stored["label"] == "phishing"
    assert stored["source_name"] == "mail.eml"
    assert stored["content_sha256"] == result["content_sha256"]
    assert stored["subject_preview"] == ""
    assert result["created_at"] == stored["created_at"]


def test_subject_preview_is_stored_only_when_requested(conn):
    service.analyze_and_store(conn, PHISHY, FakePredictor(), store_preview=True)

    assert storage.get_analysis(conn, 1)["subject_preview"] == "Verify your password"


def test_failed_analysis_stores_nothing(conn):
    with pytest.raises(EmailValidationError):
        service.analyze_and_store(conn, {"subject": "", "body": ""}, FakePredictor())

    assert storage.list_history(conn) == []


def test_analyze_many_separates_results_and_errors():
    records = [PHISHY, {"subject": "", "body": ""}, "not a dict", NORMAL]

    results, errors = service.analyze_many(records, FakePredictor())

    assert [item["index"] for item in results] == [0, 3]
    assert [item["index"] for item in errors] == [1, 2]
    assert "no usable content" in errors[0]["message"]
    assert "must be a dict" in errors[1]["message"]


def test_analyze_many_on_an_empty_list():
    assert service.analyze_many([], FakePredictor()) == ([], [])
