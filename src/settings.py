"""Application settings read from environment variables (Member 4).

Copy ``.env.example`` to ``.env`` and set the variables in your shell (or let
your tooling load the file). Nothing secret is needed; there are no API keys.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from src import explain


class SettingsError(ValueError):
    """Raised when an environment variable has an invalid value."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the API and the web app."""

    model_dir: str = "models/latest"
    db_path: str = "data/history.db"
    medium_threshold: float = 0.4
    high_threshold: float = 0.7
    decision_threshold: float = 0.5

    @property
    def thresholds(self) -> dict[str, float]:
        """Risk-level thresholds in the form ``explain`` expects."""
        return {"medium": self.medium_threshold, "high": self.high_threshold}


def _read_float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        raise SettingsError(f"{name} must be a number, got {raw!r}.") from None


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Build ``Settings`` from environment variables.

    Variables: ``MODEL_DIR``, ``DB_PATH``, ``RISK_MEDIUM``, ``RISK_HIGH``,
    ``DECISION_THRESHOLD``. Missing or blank values use the defaults.

    Raises:
        SettingsError: If a number is invalid or thresholds are inconsistent.
    """
    source = os.environ if env is None else env
    defaults = Settings()
    settings = Settings(
        model_dir=source.get("MODEL_DIR", "").strip() or defaults.model_dir,
        db_path=source.get("DB_PATH", "").strip() or defaults.db_path,
        medium_threshold=_read_float(source, "RISK_MEDIUM", defaults.medium_threshold),
        high_threshold=_read_float(source, "RISK_HIGH", defaults.high_threshold),
        decision_threshold=_read_float(source, "DECISION_THRESHOLD", defaults.decision_threshold),
    )
    try:
        explain.validate_thresholds(settings.thresholds)
    except ValueError as error:
        raise SettingsError(f"Invalid risk thresholds: {error}") from error
    if not 0 < settings.decision_threshold < 1:
        raise SettingsError("DECISION_THRESHOLD must be between 0 and 1 (exclusive).")
    return settings
