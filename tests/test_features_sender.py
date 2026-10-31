"""Tests for src/features/sender.py."""

import pytest

from src.features import sender as sf


def feats(sender):
    return sf.extract({"sender": sender})


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Alice <Alice@Example.com>", ("alice", "alice", "example.com")),
        ("bob@example.org", ("", "bob", "example.org")),
        ("support", ("", "support", "")),
        ("", ("", "", "")),
        (None, ("", "", "")),
    ],
)
def test_parse_sender(text, expected):
    assert sf.parse_sender(text) == expected


def test_has_sender_and_has_domain():
    assert feats("a@example.com")["sender_has_sender"] == 1.0
    assert feats("a@example.com")["sender_has_domain"] == 1.0
    assert feats("")["sender_has_sender"] == 0.0
    assert feats("support-team")["sender_has_sender"] == 1.0
    assert feats("support-team")["sender_has_domain"] == 0.0
    assert feats(None)["sender_has_sender"] == 0.0


def test_free_mail_detection():
    assert feats("someone@gmail.com")["sender_free_mail"] == 1.0
    assert feats("someone@company.example")["sender_free_mail"] == 0.0


def test_display_name_mismatch_flags_a_fake_domain_in_the_name():
    spoof = feats("paypal.com <alerts@evil-site.example.invalid>")
    honest = feats("example.com <hello@example.com>")
    subdomain = feats("example.com <hello@mail.example.com>")
    plain_name = feats("Alice Smith <alice@example.com>")
    dotted_person_name = feats("John.Smith <john@example.com>")

    assert spoof["sender_display_name_mismatch"] == 1.0
    assert honest["sender_display_name_mismatch"] == 0.0
    assert subdomain["sender_display_name_mismatch"] == 0.0
    assert plain_name["sender_display_name_mismatch"] == 0.0
    assert dotted_person_name["sender_display_name_mismatch"] == 0.0


def test_missing_sender_gives_all_zero_features():
    assert set(feats("").values()) == {0.0}
    assert set(feats(None).values()) == {0.0}
    assert set(sf.extract({}).values()) == {0.0}


def test_ip_domain_requires_a_valid_ip_literal():
    assert feats("a@192.0.2.10")["sender_ip_domain"] == 1.0
    assert feats("a@999.999.999.999")["sender_ip_domain"] == 0.0
    assert feats("a@example.com")["sender_ip_domain"] == 0.0


def test_local_part_digits_and_domain_shape():
    result = feats("user12345@mail.shop.example.com")

    assert result["sender_local_digit_count"] == 5.0
    assert result["sender_domain_length"] == float(len("mail.shop.example.com"))
    assert result["sender_subdomain_count"] == 2.0
    assert result["sender_hyphen_count"] == 0.0


def test_hyphens_suspicious_tld_ip_and_punycode():
    assert feats("a@secure-login-update.example.top")["sender_hyphen_count"] == 2.0
    assert feats("a@secure-login-update.example.top")["sender_suspicious_tld"] == 1.0
    assert feats("a@example.com")["sender_suspicious_tld"] == 0.0
    assert feats("a@192.0.2.10")["sender_ip_domain"] == 1.0
    assert feats("a@example.com")["sender_ip_domain"] == 0.0
    assert feats("a@xn--pypal-4ve.example")["sender_punycode"] == 1.0
    assert feats("a@example.com")["sender_punycode"] == 0.0


def test_every_feature_has_a_description_and_a_numeric_value():
    result = feats("Name <n@example.com>")

    assert set(result) == set(sf.descriptions())
    assert all(isinstance(value, float) for value in result.values())
    assert all(text.endswith(".") for text in sf.descriptions().values())


def test_feature_names_all_start_with_the_sender_prefix():
    assert all(name.startswith("sender_") for name in sf.registry.names())
