"""Content keys for finding duplicate and near-duplicate emails.

Two emails that share a key are treated as "the same email". Duplicate removal
and train/validation/test splitting both use these keys, so copies of one email
can never end up on both sides of a split (data leakage).

* ``exact_key``: same subject and body, ignoring upper/lower case and spacing.
* ``near_key``: additionally ignores URLs, email addresses, digits and
  punctuation, so mass-mailed template variations such as "Dear user 123" and
  "Dear user 456" get the same key.

Keys are SHA-256 hashes of normalized text. URLs are handled as plain text
only; nothing is ever fetched.
"""

import hashlib
import re
from collections.abc import Callable
from typing import Any

LEVELS = ("exact", "near")

_URL_RE = re.compile(r"(?:https?|hxxps?|ftp)://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_DIGITS_RE = re.compile(r"\d+")
_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_WHITESPACE_RE = re.compile(r"\s+")
_SEPARATOR = "\x1f"  # keeps subject and body from running together


def _parts(record: dict[str, Any]) -> tuple[str, str]:
    """Return (subject, body) of a record, treating missing values as ''."""
    if not isinstance(record, dict):
        raise TypeError(f"Record must be a dict, got {type(record).__name__}.")
    return str(record.get("subject") or ""), str(record.get("body") or "")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _collapse(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip().lower()


def _near_normalize(text: str) -> str:
    text = text.lower()
    text = _URL_RE.sub(" urltoken ", text)
    text = _EMAIL_RE.sub(" emailtoken ", text)
    text = _DIGITS_RE.sub("0", text)
    text = _PUNCTUATION_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def exact_key(record: dict[str, Any]) -> str:
    """Key for identical content (case and spacing are ignored)."""
    subject, body = _parts(record)
    return _digest(_collapse(subject) + _SEPARATOR + _collapse(body))


def near_key(record: dict[str, Any]) -> str:
    """Key for template-like content (URLs, addresses, digits, punctuation ignored)."""
    subject, body = _parts(record)
    return _digest(_near_normalize(subject) + _SEPARATOR + _near_normalize(body))


def key_function(level: str) -> Callable[[dict[str, Any]], str]:
    """Return ``exact_key`` or ``near_key`` for ``level`` ('exact' or 'near')."""
    if level == "exact":
        return exact_key
    if level == "near":
        return near_key
    raise ValueError(f"Unknown key level {level!r}. Use one of: {', '.join(LEVELS)}.")


def record_id(record: dict[str, Any]) -> str:
    """Short, stable ID for a record (first 16 hex characters of its exact key).

    Use this in reports instead of copying email text.
    """
    return exact_key(record)[:16]
