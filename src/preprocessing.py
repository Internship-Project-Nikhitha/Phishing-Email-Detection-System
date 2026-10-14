"""Validation and preprocessing for individual email records (Day 1).

This module checks that an email record has the expected shape, normalizes
its label to ``"phishing"`` or ``"legitimate"``, tidies the whitespace in its
text fields, and returns a record with a fixed set of fields.

Not part of this module (planned for later days): loading datasets, cleaning
or analyzing a whole dataset, splitting data, and training models.

Safety note: email text can contain malicious URLs. This module treats URLs
as plain text. It never opens, fetches, resolves, or parses them.
"""

import re
from dataclasses import dataclass
from typing import Any

LABEL_PHISHING = "phishing"
LABEL_LEGITIMATE = "legitimate"

# Accepted label spellings. Matching is case-insensitive, ignores surrounding
# whitespace, and treats "_" and "-" between words like a space (so
# "Safe_Email" matches "safe email"). Anything not listed here is rejected,
# never guessed.
# "spam" is deliberately NOT listed: spam is not the same thing as phishing.
PHISHING_LABEL_VARIANTS = ("phishing", "phish", "phishing email", "malicious", "1")
LEGITIMATE_LABEL_VARIANTS = (
    "legitimate",
    "legit",
    "ham",
    "safe",
    "safe email",
    "benign",
    "0",
)

_LABEL_LOOKUP: dict[str, str] = {
    **{variant: LABEL_PHISHING for variant in PHISHING_LABEL_VARIANTS},
    **{variant: LABEL_LEGITIMATE for variant in LEGITIMATE_LABEL_VARIANTS},
}

_WHITESPACE_RE = re.compile(r"\s+")
# Spaces, "_" and "-" count as a separator only BETWEEN letters/digits, so that
# "safe_email" matches "safe email" but "-1" is NOT turned into "1".
_LABEL_SEPARATOR_RE = re.compile(r"(?<=[^\W_])[\s_-]+(?=[^\W_])")

# Fields of the cleaned record that preprocess_email() returns.
OUTPUT_FIELDS = ("subject", "body", "sender", "label")


class EmailValidationError(ValueError):
    """Raised when an email record or collection is invalid."""


@dataclass(frozen=True)
class RecordError:
    """Describes one record that failed validation in a batch."""

    index: int  # Position of the record in the input collection (0-based).
    message: str  # Human-readable reason the record was rejected.


@dataclass(frozen=True)
class BatchResult:
    """Result of processing a collection of records."""

    valid: list[dict[str, str]]  # Cleaned records, in their original order.
    errors: list[RecordError]  # One entry per rejected record.


def normalize_text(text: str) -> str:
    """Collapse runs of whitespace into single spaces and trim the ends.

    Only whitespace is changed. Punctuation, letters, digits, and URLs are
    left exactly as they were. Newlines and tabs count as whitespace, so line
    breaks become single spaces.

    Args:
        text: The text to normalize.

    Returns:
        The normalized text. Empty or whitespace-only input gives ``""``.

    Raises:
        EmailValidationError: If ``text`` is not a string.
    """
    if not isinstance(text, str):
        raise EmailValidationError(
            f"Text must be a string, got {type(text).__name__}."
        )
    return _WHITESPACE_RE.sub(" ", text).strip()


def normalize_label(label: Any) -> str:
    """Convert a label variation into ``"phishing"`` or ``"legitimate"``.

    Args:
        label: A string (for example ``"Phishing"``, ``"safe_email"``, ``"1"``)
            or an integer (``1`` or ``0``). See ``PHISHING_LABEL_VARIANTS`` and
            ``LEGITIMATE_LABEL_VARIANTS`` for every accepted spelling.

    Returns:
        ``"phishing"`` or ``"legitimate"``.

    Raises:
        EmailValidationError: If the label is missing, empty, of an
            unsupported type (booleans are rejected), or not a known variation.
    """
    if label is None:
        raise EmailValidationError("Label is missing.")
    # bool is a subclass of int in Python, so it must be rejected first.
    if isinstance(label, bool) or not isinstance(label, (str, int)):
        raise EmailValidationError(
            f"Label must be a string or an integer, got {type(label).__name__}."
        )

    key = _LABEL_SEPARATOR_RE.sub(" ", str(label).strip().lower()).strip()
    if not key:
        raise EmailValidationError("Label is empty.")

    try:
        return _LABEL_LOOKUP[key]
    except KeyError:
        raise EmailValidationError(
            f"Unknown label {label!r}. "
            f"Supported phishing labels: {', '.join(PHISHING_LABEL_VARIANTS)}. "
            f"Supported legitimate labels: {', '.join(LEGITIMATE_LABEL_VARIANTS)}."
        ) from None


def _read_text_field(record: dict[str, Any], field_name: str) -> str:
    """Return a normalized text field, or ``""`` if it is missing or None."""
    value = record.get(field_name)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise EmailValidationError(
            f"Field '{field_name}' must be a string, got {type(value).__name__}."
        )
    return normalize_text(value)


def preprocess_email(record: dict[str, Any]) -> dict[str, str]:
    """Validate and clean a single email record.

    Expected input: a dictionary with the keys ``subject``, ``body``,
    ``sender`` and ``label``. ``subject``, ``body`` and ``sender`` are
    optional (missing or ``None`` becomes ``""``), but at least one of
    ``subject`` or ``body`` must contain text. ``label`` is required. Extra
    keys are ignored. The input dictionary is not modified.

    Args:
        record: The email record to process.

    Returns:
        A new dictionary with exactly these string fields: ``subject``,
        ``body``, ``sender`` (whitespace-normalized, otherwise unchanged) and
        ``label`` (``"phishing"`` or ``"legitimate"``).

    Raises:
        EmailValidationError: If ``record`` is not a dictionary, a text field
            is not a string, there is no usable subject or body, or the label
            is missing or not recognized.
    """
    if not isinstance(record, dict):
        raise EmailValidationError(
            f"Email record must be a dict, got {type(record).__name__}."
        )

    subject = _read_text_field(record, "subject")
    body = _read_text_field(record, "body")
    sender = _read_text_field(record, "sender")

    if not subject and not body:
        raise EmailValidationError(
            "Email has no usable content: 'subject' and 'body' are both "
            "missing or empty."
        )

    label = normalize_label(record.get("label"))

    return {"subject": subject, "body": body, "sender": sender, "label": label}


def preprocess_emails(records: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> BatchResult:
    """Validate and clean a list or tuple of email records.

    One bad record does not stop the others: each failure is recorded in
    ``errors`` with its position, and the remaining records are still
    processed.

    Args:
        records: A list or tuple of email dictionaries (see
            ``preprocess_email``).

    Returns:
        A ``BatchResult`` with the cleaned records in ``valid`` (original
        order) and one ``RecordError`` per rejected record in ``errors``. An
        empty input gives an empty result.

    Raises:
        EmailValidationError: If ``records`` itself is not a list or tuple
            (for example a single dictionary or a string).
    """
    if not isinstance(records, (list, tuple)):
        hint = (
            " Use preprocess_email() for a single record."
            if isinstance(records, dict)
            else ""
        )
        raise EmailValidationError(
            f"Expected a list or tuple of email records, got "
            f"{type(records).__name__}.{hint}"
        )

    valid: list[dict[str, str]] = []
    errors: list[RecordError] = []
    for index, record in enumerate(records):
        try:
            valid.append(preprocess_email(record))
        except EmailValidationError as error:
            errors.append(RecordError(index=index, message=str(error)))
    return BatchResult(valid=valid, errors=errors)
