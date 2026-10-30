"""Subject and body text features (Member 3).

Simple, explainable signals such as urgent wording, requests for credentials
and shouting. The keyword lists are small heuristics, not complete dictionaries.
"""

import re
from typing import Any

from src.features.base import FeatureRegistry

registry = FeatureRegistry("text")

URGENT_WORDS = (
    "urgent", "immediately", "asap", "act now", "final notice", "within 24 hours",
    "expires", "suspended", "limited", "last chance", "right away",
)
CREDENTIAL_WORDS = (
    "password", "verify", "login", "log in", "sign in", "account", "confirm",
    "security", "ssn", "social security", "pin", "credentials",
)
MONEY_WORDS = ("prize", "winner", "lottery", "payment", "invoice", "refund", "bank", "wire", "gift card", "bitcoin")

_HTML_RE = re.compile(r"(?i)<\s*(?:html|a|img|table|form|div|span|body)\b")
_FORM_RE = re.compile(r"(?i)<\s*form\b")


def extract(record: dict[str, Any]) -> dict[str, float]:
    """Return all text features for one cleaned record."""
    return registry.extract(record)


def descriptions() -> dict[str, str]:
    """Return a plain-language description for every text feature."""
    return registry.descriptions()


def _full_text(record: dict[str, Any]) -> str:
    return f"{record.get('subject', '')} {record.get('body', '')}".lower()


def count_phrases(text: str, phrases: tuple[str, ...]) -> int:
    """Count how often any of ``phrases`` appears in ``text`` as whole words (case-insensitive)."""
    lowered = text.lower()
    return sum(len(re.findall(r"\b" + re.escape(phrase) + r"\b", lowered)) for phrase in phrases)


@registry.register("subject_length", "Number of characters in the subject.")
def subject_length(record: dict[str, Any]) -> float:
    return float(len(str(record.get("subject", ""))))


@registry.register("body_words", "Number of words in the body.")
def body_words(record: dict[str, Any]) -> float:
    return float(len(str(record.get("body", "")).split()))


@registry.register("exclamations", "Number of exclamation marks, often used to create pressure.")
def exclamations(record: dict[str, Any]) -> float:
    return float(f"{record.get('subject', '')}{record.get('body', '')}".count("!"))


@registry.register("uppercase_ratio", "Share of letters that are capitals (shouting).")
def uppercase_ratio(record: dict[str, Any]) -> float:
    letters = [char for char in f"{record.get('subject', '')}{record.get('body', '')}" if char.isalpha()]
    return sum(char.isupper() for char in letters) / len(letters) if letters else 0.0


@registry.register("urgent_words", "Number of urgent or threatening phrases such as 'act now' or 'suspended'.")
def urgent_words(record: dict[str, Any]) -> float:
    return float(count_phrases(_full_text(record), URGENT_WORDS))


# @@PART 2
@registry.register("credential_words", "Number of words asking for logins, passwords or account verification.")
def credential_words(record: dict[str, Any]) -> float:
    return float(count_phrases(_full_text(record), CREDENTIAL_WORDS))


@registry.register("money_words", "Number of words about prizes, payments or money transfers.")
def money_words(record: dict[str, Any]) -> float:
    return float(count_phrases(_full_text(record), MONEY_WORDS))


@registry.register("has_html", "The body contains HTML markup.")
def has_html(record: dict[str, Any]) -> float:
    return 1.0 if _HTML_RE.search(str(record.get("body", ""))) else 0.0


@registry.register("has_form", "The body contains an HTML form, which can be used to collect passwords.")
def has_form(record: dict[str, Any]) -> float:
    return 1.0 if _FORM_RE.search(str(record.get("body", ""))) else 0.0


@registry.register("fake_reply_prefix", "The subject starts with 'Re:' or 'Fwd:', which can fake an earlier conversation.")
def fake_reply_prefix(record: dict[str, Any]) -> float:
    return 1.0 if re.match(r"(?i)^\s*(?:re|fwd?)\s*:", str(record.get("subject", ""))) else 0.0


@registry.register("digit_ratio", "Share of characters that are digits.")
def digit_ratio(record: dict[str, Any]) -> float:
    text = f"{record.get('subject', '')}{record.get('body', '')}"
    return sum(char.isdigit() for char in text) / len(text) if text else 0.0
