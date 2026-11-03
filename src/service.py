"""The analysis workflow used by both the API and the web app (Member 4).

    email dict -> clean -> features -> model score + contributions -> explanation
               -> (optional) store in history

Nothing here opens URLs, downloads anything or executes attachments. The
``predictor`` can be any object with ``version``, ``predict_score(record)`` and
``contributions(record)`` (``bundle.ModelBundle`` does; tests use a fake one).
"""

import sqlite3
from typing import Any, Protocol

from src import analysis_input, explain, keys, storage
from src.features import pipeline
from src.preprocessing import EmailValidationError


class Predictor(Protocol):
    """What the service needs from a model."""

    version: str

    def predict_score(self, record: dict[str, Any]) -> float: ...

    def contributions(self, record: dict[str, Any]) -> dict[str, float]: ...


def analyze_record(
    record: dict[str, Any],
    predictor: Predictor,
    thresholds: dict[str, float] | None = None,
    decision_threshold: float = explain.DEFAULT_DECISION_THRESHOLD,
    top_k: int = 5,
    extra_warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze one unlabeled email dict (``subject``, ``body``, ``sender``).

    Returns:
        A dict with ``score``, ``label``, ``risk_level``, ``indicators``,
        ``model_version``, ``content_sha256`` and ``warnings``.

    Raises:
        EmailValidationError: If the email has no usable content or bad types.
        ValueError: If the predictor returns a score outside 0..1.
    """
    cleaned = analysis_input.prepare_for_analysis(record)
    features = pipeline.extract_all(cleaned)
    score = predictor.predict_score(cleaned)
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
        raise ValueError(f"Predictor returned an invalid score: {score!r}.")
    result = explain.explain(
        score,
        predictor.contributions(cleaned),
        pipeline.feature_descriptions(),
        features,
        thresholds,
        decision_threshold,
        top_k,
    )
    result["model_version"] = predictor.version
    result["content_sha256"] = keys.exact_key(cleaned)
    result["warnings"] = list(extra_warnings or [])
    return result


# @@PART 2
def analyze_and_store(
    conn: sqlite3.Connection,
    record: dict[str, Any],
    predictor: Predictor,
    source_name: str = "",
    store_preview: bool = False,
    **options: Any,
) -> dict[str, Any]:
    """Analyze one email and save the result to the history database.

    Args:
        conn: Connection from ``storage.connect``.
        record: The email dict.
        predictor: The model wrapper.
        source_name: Display name (for example the uploaded file name).
        store_preview: If True, keep the first 80 characters of the subject.
        **options: Passed to ``analyze_record`` (thresholds, top_k, ...).

    Returns:
        The analysis dict, with an added ``id`` and ``created_at`` from storage.
    """
    result = analyze_record(record, predictor, **options)
    preview = analysis_input.prepare_for_analysis(record)["subject"] if store_preview else ""
    analysis_id = storage.save_analysis(
        conn, result, source_name=source_name, content_sha256=result["content_sha256"], subject_preview=preview
    )
    stored = storage.get_analysis(conn, analysis_id)
    return {**result, "id": analysis_id, "created_at": stored["created_at"] if stored else ""}


def analyze_many(
    records: list[dict[str, Any]], predictor: Predictor, **options: Any
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Analyze a list of emails; bad emails are reported, not fatal.

    Returns:
        ``(results, errors)``. ``results`` holds one dict per good email with
        its input ``index``; ``errors`` holds ``{"index", "message"}`` for each
        email that could not be analyzed.
    """
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        try:
            results.append({"index": index, **analyze_record(record, predictor, **options)})
        except (EmailValidationError, ValueError) as error:
            errors.append({"index": index, "message": str(error)})
    return results, errors
