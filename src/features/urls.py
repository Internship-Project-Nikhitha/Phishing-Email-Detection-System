"""URL features (Member 2).

URLs are analysed as TEXT ONLY. This module never opens, fetches, resolves or
follows a URL. ``urllib.parse`` is used purely to split a string into parts.
"""

import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlsplit

from src.features.base import FeatureRegistry

registry = FeatureRegistry("url")

SHORTENER_DOMAINS = frozenset(
    {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "rebrand.ly", "cutt.ly"}
)

_URL_RE = re.compile(r"(?i)\b(?:https?|hxxps?|ftp)://[^\s<>\"')]+|\bwww\.[^\s<>\"')]+")
_TRAILING_PUNCTUATION = ".,;:!?"
_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_DOMAIN_LIKE_RE = re.compile(r"(?i)\b[a-z0-9-]+(?:\.[a-z0-9-]+)+\b")


def extract(record: dict[str, Any]) -> dict[str, float]:
    """Return all URL features for one cleaned record."""
    return registry.extract(record)


def descriptions() -> dict[str, str]:
    """Return a plain-language description for every URL feature."""
    return registry.descriptions()


def find_urls(text: str) -> list[str]:
    """Return URL-looking strings found in ``text`` (as plain text, unchanged apart from trailing punctuation)."""
    return [match.rstrip(_TRAILING_PUNCTUATION) for match in _URL_RE.findall(text or "")]


def _normalize_for_parsing(url: str) -> str:
    """Undo common defanging (hxxp, [.]) and add a scheme to bare www addresses."""
    url = url.replace("[.]", ".").replace("(.)", ".")
    url = re.sub(r"(?i)^hxxp", "http", url)
    if url.lower().startswith("www."):
        url = "http://" + url
    return url


def parse_host(url: str) -> str:
    """Return the lower-case host name of ``url`` (``''`` if it cannot be parsed). Text parsing only."""
    try:
        return (urlsplit(_normalize_for_parsing(url)).hostname or "").lower()
    except ValueError:
        return ""


def _hosts(record: dict[str, Any]) -> list[str]:
    text = f"{record.get('subject', '')} {record.get('body', '')}"
    return [host for host in (parse_host(url) for url in find_urls(text)) if host]


def _urls(record: dict[str, Any]) -> list[str]:
    return find_urls(f"{record.get('subject', '')} {record.get('body', '')}")


@registry.register("count", "Number of web addresses in the email.")
def count(record: dict[str, Any]) -> float:
    return float(len(_urls(record)))


@registry.register("unique_domains", "Number of different domains linked in the email.")
def unique_domains(record: dict[str, Any]) -> float:
    return float(len(set(_hosts(record))))


@registry.register("ip_host", "A link points to a raw IP address instead of a domain name.")
def ip_host(record: dict[str, Any]) -> float:
    return 1.0 if any(_IPV4_RE.match(host) for host in _hosts(record)) else 0.0


@registry.register("has_at_symbol", "A link contains an @ sign before the host, which can hide the real destination.")
def has_at_symbol(record: dict[str, Any]) -> float:
    for url in _urls(record):
        authority = _normalize_for_parsing(url).split("://", 1)[-1].split("/", 1)[0]
        if "@" in authority:
            return 1.0
    return 0.0


@registry.register("shortener", "A link uses a URL-shortening service that hides its destination.")
def shortener(record: dict[str, Any]) -> float:
    return 1.0 if any(host in SHORTENER_DOMAINS for host in _hosts(record)) else 0.0


# @@PART 2
@registry.register("max_length", "Length of the longest web address (long addresses can hide the real domain).")
def max_length(record: dict[str, Any]) -> float:
    return float(max((len(url) for url in _urls(record)), default=0))


@registry.register("max_subdomains", "Largest number of subdomain levels in any linked domain.")
def max_subdomains(record: dict[str, Any]) -> float:
    return float(max((max(0, len(host.split(".")) - 2) for host in _hosts(record)), default=0))


@registry.register("max_hyphens", "Largest number of hyphens in any linked domain.")
def max_hyphens(record: dict[str, Any]) -> float:
    return float(max((host.count("-") for host in _hosts(record)), default=0))


@registry.register("punycode", "A link uses punycode (xn--), which can disguise look-alike characters.")
def punycode(record: dict[str, Any]) -> float:
    return 1.0 if any("xn--" in host for host in _hosts(record)) else 0.0


@registry.register("plain_http", "A link uses unencrypted http instead of https.")
def plain_http(record: dict[str, Any]) -> float:
    return 1.0 if any(re.match(r"(?i)^(?:http|hxxp)://", url) for url in _urls(record)) else 0.0


class _LinkCollector(HTMLParser):
    """Collects (href, visible text) pairs for every <a> tag. Parses text only."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._text).strip()))
            self._href = None


def find_html_links(html: str) -> list[tuple[str, str]]:
    """Return ``(href, visible_text)`` for each ``<a>`` tag in an HTML string."""
    collector = _LinkCollector()
    try:
        collector.feed(html or "")
        collector.close()
    except Exception:  # malformed markup must never crash feature extraction
        pass
    return collector.links


def _registered_domain(host: str) -> str:
    """Last two labels of a host (simple rule; no public-suffix list)."""
    return ".".join(host.split(".")[-2:])


@registry.register(
    "anchor_mismatch",
    "A link's visible text shows one domain but the link actually goes to a different domain.",
)
def anchor_mismatch(record: dict[str, Any]) -> float:
    for href, shown in find_html_links(str(record.get("body", ""))):
        real_host = parse_host(href)
        match = _DOMAIN_LIKE_RE.search(shown)
        if real_host and match:
            shown_host = parse_host(match.group(0)) or match.group(0).lower()
            if _registered_domain(shown_host) != _registered_domain(real_host):
                return 1.0
    return 0.0
