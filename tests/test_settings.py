"""Tests for src/settings.py."""

import pytest

from src import settings as cfg


def test_defaults_when_nothing_is_set():
    result = cfg.load_settings({})

    assert result == cfg.Settings()
    assert result.thresholds == {"medium": 0.4, "high": 0.7}


def test_values_are_read_from_the_environment():
    env = {
        "MODEL_DIR": "models/v2",
        "DB_PATH": "data/test.db",
        "RISK_MEDIUM": "0.3",
        "RISK_HIGH": "0.8",
        "DECISION_THRESHOLD": "0.45",
    }

    result = cfg.load_settings(env)

    assert (result.model_dir, result.db_path) == ("models/v2", "data/test.db")
    assert (result.medium_threshold, result.high_threshold, result.decision_threshold) == (0.3, 0.8, 0.45)


def test_blank_values_fall_back_to_defaults():
    assert cfg.load_settings({"MODEL_DIR": "  ", "RISK_HIGH": ""}) == cfg.Settings()


@pytest.mark.parametrize(
    "env, message",
    [
        ({"RISK_MEDIUM": "abc"}, "RISK_MEDIUM must be a number"),
        ({"RISK_MEDIUM": "0.9", "RISK_HIGH": "0.5"}, "Invalid risk thresholds"),
        ({"RISK_HIGH": "1.5"}, "Invalid risk thresholds"),
        ({"DECISION_THRESHOLD": "1"}, "DECISION_THRESHOLD must be between"),
        ({"DECISION_THRESHOLD": "x"}, "DECISION_THRESHOLD must be a number"),
    ],
)
def test_invalid_values_are_rejected_with_clear_messages(env, message):
    with pytest.raises(cfg.SettingsError, match=message):
        cfg.load_settings(env)


def test_real_environment_is_used_when_no_mapping_is_given(monkeypatch):
    monkeypatch.setenv("MODEL_DIR", "from-env")

    assert cfg.load_settings().model_dir == "from-env"
