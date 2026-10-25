"""Tests for src/features/base.py."""

import pytest

from src.features.base import FeatureRegistry


def make_registry():
    registry = FeatureRegistry("demo")

    @registry.register("has_body", "The email has a body.")
    def has_body(record):
        return bool(record.get("body"))

    @registry.register("body_words", "Number of words in the body.")
    def body_words(record):
        return len(record.get("body", "").split())

    return registry


def test_extract_returns_prefixed_float_features_in_registration_order():
    registry = make_registry()

    result = registry.extract({"body": "three small words"})

    assert list(result) == ["demo_has_body", "demo_body_words"]
    assert result == {"demo_has_body": 1.0, "demo_body_words": 3.0}
    assert all(isinstance(value, float) for value in result.values())


def test_names_and_descriptions():
    registry = make_registry()

    assert registry.names() == ["demo_has_body", "demo_body_words"]
    assert registry.descriptions()["demo_body_words"] == "Number of words in the body."


def test_duplicate_and_invalid_registrations_are_rejected():
    registry = make_registry()

    with pytest.raises(ValueError, match="already registered"):
        registry.register("has_body", "again")(lambda record: 0)
    with pytest.raises(ValueError, match="valid identifier"):
        registry.register("bad name", "x")(lambda record: 0)
    with pytest.raises(ValueError, match="needs a description"):
        registry.register("ok_name", "  ")(lambda record: 0)
    with pytest.raises(ValueError, match="non-empty string description"):
        registry.register("bad_description", None)


def test_invalid_prefix_is_rejected():
    for prefix in ("", "not valid", "1abc"):
        with pytest.raises(ValueError, match="prefix"):
            FeatureRegistry(prefix)


def test_extract_rejects_non_dict_records():
    with pytest.raises(TypeError, match="must be a dict"):
        make_registry().extract("text")


def test_empty_registry_extracts_an_empty_dict():
    assert FeatureRegistry("empty").extract({}) == {}
