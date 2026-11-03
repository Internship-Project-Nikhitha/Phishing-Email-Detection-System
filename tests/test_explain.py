"""Tests for src/explain.py."""

import pytest

from src import explain as ex


@pytest.mark.parametrize(
    "score, expected",
    [(0.0, "low"), (0.39, "low"), (0.4, "medium"), (0.69, "medium"), (0.7, "high"), (1.0, "high")],
)
def test_risk_level_with_default_thresholds(score, expected):
    assert ex.risk_level(score) == expected


def test_risk_level_with_custom_thresholds():
    assert ex.risk_level(0.5, {"medium": 0.6, "high": 0.9}) == "low"
    assert ex.risk_level(0.95, {"medium": 0.6, "high": 0.9}) == "high"


@pytest.mark.parametrize("score", [-0.1, 1.1, "0.5", None, True])
def test_risk_level_rejects_bad_scores(score):
    with pytest.raises(ValueError, match="Score must be"):
        ex.risk_level(score)


@pytest.mark.parametrize(
    "thresholds",
    [{"medium": 0.7, "high": 0.4}, {"medium": 0.0, "high": 0.5}, {"medium": 0.5, "high": 1.5}, {"medium": 0.5}],
)
def test_validate_thresholds_rejects_bad_settings(thresholds):
    with pytest.raises(ValueError):
        ex.validate_thresholds(thresholds)


# @@PART 2
DESCRIPTIONS = {"url_count": "Number of web addresses.", "text_urgent_words": "Urgent wording."}


def test_describe_feature_known_unknown_and_word_features():
    assert ex.describe_feature("url_count", DESCRIPTIONS) == "Number of web addresses."
    assert ex.describe_feature("mystery", DESCRIPTIONS) == "mystery"
    assert '"password"' in ex.describe_feature("word:password", DESCRIPTIONS)


def test_top_indicators_orders_by_strength_and_skips_non_positive():
    contributions = {"url_count": 0.5, "text_urgent_words": 1.2, "sender_free_mail": -0.4, "word:zero": 0.0}

    result = ex.top_indicators(contributions, DESCRIPTIONS, features={"url_count": 3.0}, k=5)

    assert [item["feature"] for item in result] == ["text_urgent_words", "url_count"]
    assert result[1] == {
        "feature": "url_count",
        "description": "Number of web addresses.",
        "contribution": 0.5,
        "value": 3.0,
    }
    assert result[0]["value"] is None


def test_top_indicators_respects_k_and_breaks_ties_by_name():
    contributions = {"b": 1.0, "a": 1.0, "c": 0.5}

    assert [i["feature"] for i in ex.top_indicators(contributions, {}, k=2)] == ["a", "b"]
    with pytest.raises(ValueError, match="at least 1"):
        ex.top_indicators(contributions, {}, k=0)


def test_explain_builds_the_full_result():
    result = ex.explain(0.83, {"url_count": 0.5}, DESCRIPTIONS, features={"url_count": 2.0})

    assert result["label"] == "phishing"
    assert result["risk_level"] == "high"
    assert result["score"] == 0.83
    assert result["indicators"][0]["feature"] == "url_count"


def test_explain_low_score_is_legitimate_and_may_have_no_indicators():
    result = ex.explain(0.05, {"url_count": -0.3}, DESCRIPTIONS)

    assert (result["label"], result["risk_level"], result["indicators"]) == ("legitimate", "low", [])


def test_explain_respects_the_decision_threshold():
    assert ex.explain(0.45, {}, {}, decision_threshold=0.4)["label"] == "phishing"
    assert ex.explain(0.45, {}, {}, decision_threshold=0.5)["label"] == "legitimate"
    with pytest.raises(ValueError, match="decision_threshold"):
        ex.explain(0.5, {}, {}, decision_threshold=1.0)
