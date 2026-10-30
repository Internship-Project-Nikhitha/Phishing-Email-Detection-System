"""Sender features (Member 1).

Everything here is computed from the sender *text* only. No DNS lookups, no
network requests, and the sender is never contacted.
"""

import re
from email.utils import parseaddr
from typing import Any

from src.features.base import FeatureRegistry

registry = FeatureRegistry("sender")

# Heuristic lists. They are examples of common patterns, not complete or
# authoritative; document any change in docs/features-sender.md.
FREE_MAIL_DOMAINS = frozenset(
    {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "proton.me",
     "protonmail.com", "icloud.com", "mail.com", "gmx.com"}
)
SUSPICIOUS_TLDS = frozenset(
    {"zip", "mov", "top", "xyz", "click", "work", "loan", "gq", "tk", "ml", "cf", "ga", "icu", "rest"}
)

_IPV4_RE = re.compile(r"^\[?\d{1,3}(?:\.\d{1,3}){3}\]?$")
_DOMAIN_IN_TEXT_RE = re.compile(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+")


def extract(record: dict[str, Any]) -> dict[str, float]:
    """Return all sender features for one cleaned record."""
    return registry.extract(record)


def descriptions() -> dict[str, str]:
    """Return a plain-language description for every sender feature."""
    return registry.descriptions()


def parse_sender(sender: str) -> tuple[str, str, str]:
    """Split a sender string into ``(display_name, local_part, domain)``.

    All three parts are lower-case. Missing parts are ``''``. A value without
    an ``@`` is treated as a bare identifier (no domain).

    Example:
        ``'Alice <Alice@Example.com>'`` gives ``('alice', 'alice', 'example.com')``.
    """
    name, address = parseaddr(sender or "")
    address = address.strip().lower()
    display = name.strip().lower()
    if "@" not in address:
        return display, address, ""
    local, _, domain = address.rpartition("@")
    return display, local, domain.strip(".")


def _domain(record: dict[str, Any]) -> str:
    return parse_sender(record.get("sender", ""))[2]


@registry.register("has_sender", "The email has a sender value.")
def has_sender(record: dict[str, Any]) -> float:
    return 1.0 if str(record.get("sender", "")).strip() else 0.0


@registry.register("has_domain", "The sender looks like an email address with a domain.")
def has_domain(record: dict[str, Any]) -> float:
    return 1.0 if _domain(record) else 0.0


@registry.register("free_mail", "The sender uses a free webmail provider.")
def free_mail(record: dict[str, Any]) -> float:
    return 1.0 if _domain(record) in FREE_MAIL_DOMAINS else 0.0


@registry.register(
    "display_name_mismatch",
    "The display name contains a web address or email address that differs from the real sender domain.",
)
def display_name_mismatch(record: dict[str, Any]) -> float:
    display, _, domain = parse_sender(record.get("sender", ""))
    if not display or not domain:
        return 0.0
    for shown in _DOMAIN_IN_TEXT_RE.findall(display):
        if not (shown == domain or domain.endswith("." + shown) or shown.endswith("." + domain)):
            return 1.0
    return 0.0


# @@PART 2
@registry.register("local_digit_count", "Number of digits in the part of the address before the @ sign.")
def local_digit_count(record: dict[str, Any]) -> float:
    local = parse_sender(record.get("sender", ""))[1]
    return float(sum(char.isdigit() for char in local))


@registry.register("domain_length", "Length of the sender domain; very long domains are often auto-generated.")
def domain_length(record: dict[str, Any]) -> float:
    return float(len(_domain(record)))


@registry.register("subdomain_count", "Number of subdomain levels in the sender domain (mail.shop.example.com has 2).")
def subdomain_count(record: dict[str, Any]) -> float:
    domain = _domain(record)
    return float(max(0, len(domain.split(".")) - 2)) if domain else 0.0


@registry.register("hyphen_count", "Number of hyphens in the sender domain.")
def hyphen_count(record: dict[str, Any]) -> float:
    return float(_domain(record).count("-"))


@registry.register("suspicious_tld", "The sender domain ends in a top-level domain often used in abuse.")
def suspicious_tld(record: dict[str, Any]) -> float:
    domain = _domain(record)
    return 1.0 if domain and domain.rsplit(".", 1)[-1] in SUSPICIOUS_TLDS else 0.0


@registry.register("ip_domain", "The sender 'domain' is a raw IP address.")
def ip_domain(record: dict[str, Any]) -> float:
    return 1.0 if _IPV4_RE.match(_domain(record)) else 0.0


@registry.register("punycode", "The sender domain uses punycode (xn--), which can disguise look-alike characters.")
def punycode(record: dict[str, Any]) -> float:
    return 1.0 if "xn--" in _domain(record) else 0.0
