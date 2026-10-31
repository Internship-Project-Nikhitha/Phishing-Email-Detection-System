"""Tests for src/features/urls.py."""

import socket
import urllib.request

import pytest

from src.features import urls as uf


def feats(body, subject=""):
    return uf.extract({"subject": subject, "body": body})


def test_find_urls_strips_trailing_punctuation_and_keeps_the_text():
    text = "Go to http://a.example.invalid/x?y=1, or www.b.example.invalid. Also hxxp://c[.]example[.]invalid/z!"

    assert uf.find_urls(text) == [
        "http://a.example.invalid/x?y=1",
        "www.b.example.invalid",
        "hxxp://c[.]example[.]invalid/z",
    ]
    assert uf.find_urls("") == []
    assert uf.find_urls(None) == []


@pytest.mark.parametrize(
    "url, host",
    [
        ("http://User:Pass@Evil.Example.invalid:8080/path", "evil.example.invalid"),
        ("www.example.invalid/page", "www.example.invalid"),
        ("hxxps://bad[.]example[.]invalid/a", "bad.example.invalid"),
        ("http://192.0.2.7/login", "192.0.2.7"),
        ("http://[broken", ""),
    ],
)
def test_parse_host(url, host):
    assert uf.parse_host(url) == host


def test_count_and_unique_domains():
    body = "http://a.example.invalid/1 http://a.example.invalid/2 http://b.example.invalid"

    result = feats(body)

    assert result["url_count"] == 3.0
    assert result["url_unique_domains"] == 2.0


def test_subject_urls_are_counted_too():
    assert feats("no links here", subject="see http://x.example.invalid")["url_count"] == 1.0


def test_ip_host_at_symbol_and_shortener():
    assert feats("http://192.0.2.7/login")["url_ip_host"] == 1.0
    assert feats("http://example.invalid/login")["url_ip_host"] == 0.0
    assert feats("http://paypal.com@evil.example.invalid/x")["url_has_at_symbol"] == 1.0
    assert feats("http://evil.example.invalid/a@b")["url_has_at_symbol"] == 0.0
    assert feats("https://bit.ly/abc123")["url_shortener"] == 1.0
    assert feats("https://example.invalid/abc123")["url_shortener"] == 0.0


def test_no_urls_gives_all_zero_features():
    assert set(feats("plain text with no links").values()) == {0.0}
    assert set(uf.extract({}).values()) == {0.0}


# @@PART 2
def test_length_subdomain_hyphen_punycode_and_http():
    url = "http://login.secure-update.account-check.example.invalid/very/long/path?token=abcdef"

    result = feats(url)

    assert result["url_max_length"] == float(len(url))
    assert result["url_max_subdomains"] == 3.0
    assert result["url_max_hyphens"] == 2.0
    assert result["url_plain_http"] == 1.0
    assert result["url_punycode"] == 0.0
    assert feats("https://example.invalid")["url_plain_http"] == 0.0
    assert feats("http://xn--pypal-4ve.example.invalid")["url_punycode"] == 1.0


def test_find_html_links_returns_href_and_visible_text():
    html = '<p>Hi <a href="http://real.example.invalid/x">www.bank.example.invalid</a> and <a href="/rel">Click</a></p>'

    assert uf.find_html_links(html) == [
        ("http://real.example.invalid/x", "www.bank.example.invalid"),
        ("/rel", "Click"),
    ]


def test_find_html_links_survives_malformed_html():
    assert uf.find_html_links("<a href='x'>unclosed <b><<<") is not None
    assert uf.find_html_links("") == []


def test_anchor_mismatch_detects_text_that_shows_a_different_domain():
    spoof = '<a href="http://evil.example.invalid/login">www.mybank.example.com</a>'
    honest = '<a href="http://www.mybank.example.com/login">www.mybank.example.com</a>'
    same_site = '<a href="https://secure.mybank.example.com/x">mybank.example.com</a>'
    no_domain_text = '<a href="http://evil.example.invalid">Click here</a>'

    assert feats(spoof)["url_anchor_mismatch"] == 1.0
    assert feats(honest)["url_anchor_mismatch"] == 0.0
    assert feats(same_site)["url_anchor_mismatch"] == 0.0
    assert feats(no_domain_text)["url_anchor_mismatch"] == 0.0


def test_url_features_never_touch_the_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network access attempted while extracting URL features.")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)

    result = feats('visit http://evil.example.invalid/x <a href="http://evil.example.invalid">www.good.example.com</a>')

    assert result["url_count"] >= 1.0


def test_every_feature_has_a_description_and_the_url_prefix():
    result = feats("http://x.example.invalid")

    assert set(result) == set(uf.descriptions())
    assert all(name.startswith("url_") for name in result)
