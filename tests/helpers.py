"""Shared test helpers (not a test file)."""

from typing import Any


class FakePredictor:
    """A stand-in for a trained model so app code can be tested without scikit-learn.

    If ``score`` is given it is always returned. Otherwise the score is 0.95
    when the email mentions "password" or "verify", else 0.05.
    """

    version = "fake-1"

    def __init__(self, score: float | None = None, contributions: dict[str, float] | None = None) -> None:
        self._score = score
        self._contributions = contributions

    def predict_score(self, record: dict[str, Any]) -> float:
        if self._score is not None:
            return self._score
        text = f"{record.get('subject', '')} {record.get('body', '')}".lower()
        return 0.95 if ("password" in text or "verify" in text) else 0.05

    def contributions(self, record: dict[str, Any]) -> dict[str, float]:
        if self._contributions is not None:
            return dict(self._contributions)
        return {"text_credential_words": 0.8, "url_count": 0.5, "sender_free_mail": -0.2, "word:password": 0.9}
