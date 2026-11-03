"""Risk levels and plain-language explanations (Member 1).

Turns a model score (0 to 1) and per-feature contributions into something an
analyst can read: a risk level, a label and a short list of warning indicators.

Indicators are always features the model actually used (they come from the
model's own contributions, see ``models.contributions``), so explanations are
traceable to the model rather than invented afterwards.
"""

from typing import Any

DEFAULT_THRESHOLDS = {"medium": 0.4, "high": 0.7}
DEFAULT_DECISION_THRESHOLD = 0.5


def validate_thresholds(thresholds: dict[str, float] | None = None) -> dict[str, float]:
    """Return valid risk thresholds (``0 < medium < high <= 1``).

    Raises:
        ValueError: If a threshold is missing or out of order.
    """
    chosen = dict(DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    for name in ("medium", "high"):
        if name not in chosen or isinstance(chosen[name], bool) or not isinstance(chosen[name], (int, float)):
            raise ValueError(f"Threshold '{name}' must be a number.")
    if not 0 < chosen["medium"] < chosen["high"] <= 1:
        raise ValueError("Thresholds must satisfy 0 < medium < high <= 1.")
    return {"medium": float(chosen["medium"]), "high": float(chosen["high"])}


def risk_level(score: float, thresholds: dict[str, float] | None = None) -> str:
    """Return ``'low'``, ``'medium'`` or ``'high'`` for a score between 0 and 1.

    Raises:
        ValueError: If the score is not a number in [0, 1] or thresholds are invalid.
    """
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
        raise ValueError(f"Score must be a number between 0 and 1, got {score!r}.")
    limits = validate_thresholds(thresholds)
    if score >= limits["high"]:
        return "high"
    if score >= limits["medium"]:
        return "medium"
    return "low"


# @@PART 2
def describe_feature(name: str, descriptions: dict[str, str]) -> str:
    """Return a readable description of a feature name.

    ``word:<term>`` features (text model vocabulary) get a generated sentence;
    others are looked up in ``descriptions`` and fall back to the raw name.
    """
    if name.startswith("word:"):
        return f'The word or phrase "{name[5:]}" is associated with phishing by the model.'
    return descriptions.get(name, name)


def top_indicators(
    contributions: dict[str, float],
    descriptions: dict[str, str],
    features: dict[str, float] | None = None,
    k: int = 5,
) -> list[dict[str, Any]]:
    """Pick the strongest features pointing toward phishing.

    Args:
        contributions: Feature name -> contribution (positive = toward phishing).
        descriptions: Feature name -> description.
        features: Optional raw feature values to show next to each indicator.
        k: Maximum number of indicators.

    Returns:
        Up to ``k`` dicts with ``feature``, ``description``, ``contribution``
        (rounded) and ``value``, strongest first. Only positive contributions
        are included.

    Raises:
        ValueError: If ``k`` is less than 1.
    """
    if k < 1:
        raise ValueError("k must be at least 1.")
    positive = [(name, value) for name, value in contributions.items() if value > 0]
    positive.sort(key=lambda item: (-item[1], item[0]))
    return [
        {
            "feature": name,
            "description": describe_feature(name, descriptions),
            "contribution": round(value, 4),
            "value": None if features is None else features.get(name),
        }
        for name, value in positive[:k]
    ]


def explain(
    score: float,
    contributions: dict[str, float],
    descriptions: dict[str, str],
    features: dict[str, float] | None = None,
    thresholds: dict[str, float] | None = None,
    decision_threshold: float = DEFAULT_DECISION_THRESHOLD,
    k: int = 5,
) -> dict[str, Any]:
    """Build the analyst-facing result for one email.

    Returns:
        A dict with ``score`` (rounded to 4 places), ``label``
        (``'phishing'`` if the score reaches ``decision_threshold``, otherwise
        ``'legitimate'``), ``risk_level`` and ``indicators``.
    """
    if not 0 < decision_threshold < 1:
        raise ValueError("decision_threshold must be between 0 and 1 (exclusive).")
    level = risk_level(score, thresholds)
    return {
        "score": round(float(score), 4),
        "label": "phishing" if score >= decision_threshold else "legitimate",
        "risk_level": level,
        "indicators": top_indicators(contributions, descriptions, features, k),
    }
