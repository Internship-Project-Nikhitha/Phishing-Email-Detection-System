"""Contract of the analysis service: what callers (API, web app) can rely on."""

import copy
import json

import pytest

from src import service
from src.preprocessing import EmailValidationError
from tests.helpers import FakePredictor

EMAIL = {"subject": "Verify your password", "body": "Click http://login.example.invalid/now", "sender": "a@example.com"}
RESULT_KEYS = {"score", "label", "risk_level", "indicators", "model_version", "content_sha256", "warnings"}


def test_result_has_exactly_the_documented_keys():
    assert set(service.analyze_record(EMAIL, FakePredictor())) == RESULT_KEYS


def test_result_is_json_serializable():
    result = service.analyze_record(EMAIL, FakePredictor())

    assert json.loads(json.dumps(result)) == result


def test_input_record_is_not_modified():
    record = copy.deepcopy(EMAIL)
    record["label"] = "phishing"
    before = copy.deepcopy(record)

    service.analyze_record(record, FakePredictor())

    assert record == before


def test_label_in_the_input_is_ignored():
    labeled = {**EMAIL, "label": "legitimate"}

    assert service.analyze_record(labeled, FakePredictor()) == service.analyze_record(EMAIL, FakePredictor())


def test_same_email_twice_gives_identical_results():
    assert service.analyze_record(EMAIL, FakePredictor()) == service.analyze_record(EMAIL, FakePredictor())


@pytest.mark.parametrize(
    "score, label",
    [(0.0, "legitimate"), (0.4999, "legitimate"), (0.5, "phishing"), (0.5001, "phishing"), (1.0, "phishing")],
)
def test_label_switches_exactly_at_the_decision_threshold(score, label):
    assert service.analyze_record(EMAIL, FakePredictor(score=score))["label"] == label


def test_a_custom_decision_threshold_moves_the_label_boundary():
    result = service.analyze_record(EMAIL, FakePredictor(score=0.6), decision_threshold=0.8)

    assert result["label"] == "legitimate"


@pytest.mark.parametrize(
    "score, level",
    [(0.0, "low"), (0.3999, "low"), (0.4, "medium"), (0.6999, "medium"), (0.7, "high"), (1.0, "high")],
)
def test_risk_level_boundaries_use_the_default_thresholds(score, level):
    assert service.analyze_record(EMAIL, FakePredictor(score=score))["risk_level"] == level


def test_top_k_limits_the_number_of_indicators():
    contributions = {f"feature_{n}": 1.0 + n for n in range(10)}

    result = service.analyze_record(EMAIL, FakePredictor(contributions=contributions), top_k=3)

    assert [item["feature"] for item in result["indicators"]] == ["feature_9", "feature_8", "feature_7"]


def test_only_features_pointing_toward_phishing_become_indicators():
    contributions = {"a": -2.0, "b": 0.0, "c": 0.5}

    result = service.analyze_record(EMAIL, FakePredictor(contributions=contributions))

    assert [item["feature"] for item in result["indicators"]] == ["c"]


def test_extra_warnings_are_copied_not_shared():
    warnings = ["first"]

    result = service.analyze_record(EMAIL, FakePredictor(), extra_warnings=warnings)
    warnings.append("added later")

    assert result["warnings"] == ["first"]


def test_no_extra_warnings_gives_an_empty_list_each_time():
    first = service.analyze_record(EMAIL, FakePredictor())
    first["warnings"].append("mutated")

    assert service.analyze_record(EMAIL, FakePredictor())["warnings"] == []


def test_content_hash_ignores_spacing_but_not_wording():
    spaced = {**EMAIL, "body": EMAIL["body"].replace(" ", "   ")}
    changed = {**EMAIL, "body": EMAIL["body"] + " extra"}
    base = service.analyze_record(EMAIL, FakePredictor())["content_sha256"]

    assert service.analyze_record(spaced, FakePredictor())["content_sha256"] == base
    assert service.analyze_record(changed, FakePredictor())["content_sha256"] != base
    assert len(base) == 64 and set(base) <= set("0123456789abcdef")


def test_result_does_not_repeat_the_email_text_sender_or_links():
    record = {"subject": "Zebrafish notice", "body": "Quokka http://tracker.example.invalid/q", "sender": "pangolin@example.com"}

    dump = json.dumps(service.analyze_record(record, FakePredictor())).lower()

    for secret in ("zebrafish", "quokka", "tracker.example.invalid", "pangolin"):
        assert secret not in dump


@pytest.mark.parametrize("score", [-0.1, 1.1, True, "0.5", None, float("nan")])
def test_invalid_predictor_scores_are_rejected(score):
    class Broken(FakePredictor):
        def predict_score(self, record):
            return score

    with pytest.raises(ValueError, match="invalid score"):
        service.analyze_record(EMAIL, Broken())


def test_model_version_comes_from_the_predictor():
    class Versioned(FakePredictor):
        version = "v-test-9"

    assert service.analyze_record(EMAIL, Versioned())["model_version"] == "v-test-9"


def test_analyze_many_keeps_original_indices_when_some_emails_fail():
    records = [EMAIL, "not a dict", {"subject": ""}, {**EMAIL, "subject": "Second"}, None]

    results, errors = service.analyze_many(records, FakePredictor())

    assert [item["index"] for item in results] == [0, 3]
    assert [item["index"] for item in errors] == [1, 2, 4]
    assert all(item["message"] for item in errors)


def test_analyze_many_passes_options_to_every_email():
    results, _ = service.analyze_many([EMAIL, EMAIL], FakePredictor(score=0.6), decision_threshold=0.9)

    assert [item["label"] for item in results] == ["legitimate", "legitimate"]


def test_analyze_many_does_not_hide_a_predictor_bug():
    class Crashing(FakePredictor):
        def predict_score(self, record):
            raise RuntimeError("model crashed")

    with pytest.raises(RuntimeError):
        service.analyze_many([EMAIL], Crashing())


def test_analyze_record_raises_validation_error_for_empty_content():
    with pytest.raises(EmailValidationError):
        service.analyze_record({"subject": " ", "body": "\n"}, FakePredictor())


def test_failed_analysis_does_not_consume_a_history_id():
    from src import storage

    conn = storage.connect()
    with pytest.raises(EmailValidationError):
        service.analyze_and_store(conn, {"subject": ""}, FakePredictor())
    stored = service.analyze_and_store(conn, EMAIL, FakePredictor())

    assert stored["id"] == 1 and stored["created_at"]
    conn.close()
