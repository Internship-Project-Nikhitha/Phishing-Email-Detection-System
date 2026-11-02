"""Tests for src/vectorize.py (skipped if scikit-learn is not installed)."""

import pytest

pytest.importorskip("sklearn")

from src import vectorize as vz  # noqa: E402


def recs():
    return [
        {"subject": "Verify your password", "body": "Log in at http://x.example.invalid now!", "sender": "a@bad.example.top", "label": "phishing"},
        {"subject": "Meeting notes", "body": "Attached are the notes", "sender": "b@example.com", "label": "legitimate"},
        {"subject": "Prize winner", "body": "Claim your prize today", "sender": "c@gmail.com", "label": "phishing"},
    ]


def test_text_features_shape_and_names():
    features = vz.TextFeatures()

    matrix = features.fit_transform(recs())

    assert matrix.shape == (3, len(features.names))
    assert all(name.startswith("word:") for name in features.names)
    assert "word:password" in features.names


def test_text_features_transform_unseen_text_uses_training_vocabulary():
    features = vz.TextFeatures().fit(recs())

    matrix = features.transform([{"subject": "completely unknown words", "body": "zzz"}])

    assert matrix.shape == (1, len(features.names))
    assert matrix.nnz == 0


def test_fit_on_empty_records_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        vz.TextFeatures().fit([])


# @@PART 2
from src.features import pipeline  # noqa: E402


def test_engineered_features_match_the_pipeline_feature_names():
    features = vz.EngineeredFeatures()

    matrix = features.fit_transform(recs())

    assert matrix.shape == (3, len(pipeline.feature_names()))
    assert sorted(features.names) == sorted(pipeline.feature_names())
    assert abs(matrix).max() <= 1.0 + 1e-9


@pytest.mark.parametrize("mode", ["text", "engineered", "combined"])
def test_feature_builder_modes_have_consistent_shapes(mode):
    builder = vz.FeatureBuilder(mode=mode)

    train = builder.fit_transform(recs())
    new = builder.transform([recs()[0]])

    assert train.shape == (3, len(builder.feature_names))
    assert new.shape == (1, len(builder.feature_names))


def test_combined_mode_is_text_columns_followed_by_engineered_columns():
    builder = vz.FeatureBuilder(mode="combined").fit(recs())

    names = builder.feature_names

    word_count = sum(name.startswith("word:") for name in names)
    assert all(name.startswith("word:") for name in names[:word_count])
    assert not any(name.startswith("word:") for name in names[word_count:])
    assert len(names) - word_count == len(pipeline.feature_names())


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError, match="Unknown mode"):
        vz.FeatureBuilder(mode="magic")
