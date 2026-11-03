"""Tests for src/models.py (skipped if scikit-learn is not installed)."""

import pytest

pytest.importorskip("sklearn")

from src import models as md  # noqa: E402


def rec(subject, body, label, sender="a@example.com"):
    return {"subject": subject, "body": body, "sender": sender, "label": label}


def make_data():
    phishing = [
        rec(f"Verify password {w}", f"Urgent! Confirm your account password at http://{w}.example.invalid/login now", "phishing", f"x@{w}-secure.example.top")
        for w in ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel")
    ]
    legit = [
        rec(f"Meeting notes {w}", f"Hi team, notes for the {w} planning meeting are attached. Thanks.", "legitimate")
        for w in ("india", "juliet", "kilo", "lima", "mike", "november", "oscar", "papa")
    ]
    return phishing + legit


def split(data):
    train = data[:5] + data[8:13]
    validation = data[5:8] + data[13:16]
    return train, validation


def test_available_models_has_the_four_candidates():
    names = set(md.available_models())

    assert names == {"logreg_combined", "tfidf_logreg", "tfidf_naive_bayes", "random_forest_engineered"}


@pytest.mark.parametrize("name", ["logreg_combined", "tfidf_logreg", "tfidf_naive_bayes", "random_forest_engineered"])
def test_each_model_trains_and_scores_between_zero_and_one(name):
    data = make_data()
    spec = md.available_models()[name]

    model = md.train_model(spec, data)
    scores = model.predict_scores(data)

    assert len(scores) == len(data)
    assert all(0.0 <= s <= 1.0 for s in scores)
    assert model.predict_labels(data[:1]) in (["phishing"], ["legitimate"])


def test_models_separate_an_easy_dataset():
    data = make_data()
    model = md.train_model(md.available_models()["logreg_combined"], data)

    assert model.predict_labels(data) == [r["label"] for r in data]


def test_train_model_rejects_empty_and_single_label_data():
    spec = md.available_models()["tfidf_logreg"]
    with pytest.raises(ValueError, match="empty"):
        md.train_model(spec, [])
    with pytest.raises(ValueError, match="both"):
        md.train_model(spec, [rec("a", "b", "phishing")])


def test_training_is_reproducible():
    data = make_data()
    spec = md.available_models()["random_forest_engineered"]

    first = md.train_model(spec, data, seed=5).predict_scores(data)
    second = md.train_model(spec, data, seed=5).predict_scores(data)

    assert first == second


# @@PART 2
def test_tune_model_picks_a_parameter_set_from_the_grid_using_validation_only():
    data = make_data()
    train, validation = split(data)
    spec = md.available_models()["tfidf_logreg"]

    result = md.tune_model(spec, train, validation)

    assert result.params in list(spec.param_grid)
    assert result.candidates_tried == len(spec.param_grid)
    counts = result.validation_metrics
    assert counts["tp"] + counts["fp"] + counts["tn"] + counts["fn"] == len(validation)


def test_evaluate_model_threshold_changes_predictions():
    data = make_data()
    model = md.train_model(md.available_models()["logreg_combined"], data)

    strict = md.evaluate_model(model, data, threshold=0.999999)
    lenient = md.evaluate_model(model, data, threshold=0.000001)

    assert lenient["tp"] + lenient["fp"] >= strict["tp"] + strict["fp"]


# @@PART 3
def test_logreg_contributions_point_toward_phishing_for_phishing_features():
    data = make_data()
    model = md.train_model(md.available_models()["logreg_combined"], data)
    phishing_email = data[0]

    result = md.contributions(model, phishing_email)

    assert result
    assert sum(result.values()) > 0
    assert any(name.startswith("word:") for name in result)
    assert any(not name.startswith("word:") for name in result)


def test_text_only_models_explain_with_words():
    data = make_data()
    for name in ("tfidf_logreg", "tfidf_naive_bayes"):
        model = md.train_model(md.available_models()[name], data)

        result = md.contributions(model, data[0])

        assert result and all(key.startswith("word:") for key in result)
        assert max(result.values()) > 0


def test_forest_contributions_are_importances_of_active_engineered_features():
    data = make_data()
    model = md.train_model(md.available_models()["random_forest_engineered"], data)

    result = md.contributions(model, data[0])

    assert result
    assert all(value >= 0 for value in result.values())
    assert not any(key.startswith("word:") for key in result)
