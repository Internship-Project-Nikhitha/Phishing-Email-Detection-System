"""Clean one email for analysis when it has no label (team-lead owned).

``preprocessing.preprocess_email`` is for labeled dataset rows and requires a
label. Emails uploaded for analysis have no label, so this module applies the
same text cleaning (``normalize_text``) and the same content rules without
asking for one.
"""

from typing import Any

from src.preprocessing import EmailValidationError, normalize_text

TEXT_FIELDS = ("subject", "body", "sender")


def prepare_for_analysis(record: dict[str, Any]) -> dict[str, str]:
    """Validate and clean one unlabeled email record.

    Args:
        record: A dict with optional ``subject``, ``body`` and ``sender`` text.
            Extra keys (including ``label``) are ignored.

    Returns:
        A new dict with exactly ``subject``, ``body`` and ``sender`` strings
        (whitespace-normalized; missing values become ``''``).

    Raises:
        EmailValidationError: If ``record`` is not a dict, a text field is not
            a string, or both subject and body are empty.
    """
    if not isinstance(record, dict):
        raise EmailValidationError(f"Email record must be a dict, got {type(record).__name__}.")
    cleaned: dict[str, str] = {}
    for name in TEXT_FIELDS:
        value = record.get(name)
        if value is None:
            cleaned[name] = ""
        elif isinstance(value, str):
            cleaned[name] = normalize_text(value)
        else:
            raise EmailValidationError(f"Field '{name}' must be a string, got {type(value).__name__}.")
    if not cleaned["subject"] and not cleaned["body"]:
        raise EmailValidationError(
            "Email has no usable content: 'subject' and 'body' are both missing or empty."
        )
    return cleaned
