"""Tests for src/keys.py."""

import pytest

from src import keys


def make(subject="Hello", body="World"):
    return {"subject": subject, "body": body, "sender": "", "label": "legitimate"}


def test_exact_key_is_stable_and_hex():
    key = keys.exact_key(make())

    assert key == keys.exact_key(make())
    assert len(key) == 64
    assert all(char in "0123456789abcdef" for char in key)


def test_exact_key_ignores_case_and_spacing_but_not_words():
    base = keys.exact_key(make("Account  Alert", "Please\nverify now"))

    assert base == keys.exact_key(make("account alert", "please verify   now"))
    assert base != keys.exact_key(make("Account Alert", "Please verify later"))


def test_exact_key_distinguishes_subject_from_body():
    assert keys.exact_key(make("a", "b")) != keys.exact_key(make("a b", ""))


def test_exact_key_ignores_label_and_sender():
    first = make()
    second = dict(first, label="phishing", sender="x@example.com")

    assert keys.exact_key(first) == keys.exact_key(second)


def test_near_key_ignores_digits_urls_addresses_and_punctuation():
    first = make("Dear user 123", "Visit http://a.example.invalid/x?id=1 or mail help@example.com now!")
    second = make("Dear user 987", "Visit http://b.example.invalid/y?id=22 or mail other@example.org now.")

    assert keys.near_key(first) == keys.near_key(second)
    assert keys.exact_key(first) != keys.exact_key(second)


def test_near_key_still_separates_different_wording():
    assert keys.near_key(make("Verify account", "Click here")) != keys.near_key(
        make("Team lunch", "Noon at the cafe")
    )


def test_missing_fields_are_treated_as_empty():
    assert keys.exact_key({"body": "x"}) == keys.exact_key({"subject": None, "body": "x"})
    assert keys.near_key({"subject": "x"}) == keys.near_key({"subject": "x", "body": ""})


def test_key_function_selects_level():
    assert keys.key_function("exact") is keys.exact_key
    assert keys.key_function("near") is keys.near_key


def test_key_function_rejects_unknown_level():
    with pytest.raises(ValueError, match="Unknown key level"):
        keys.key_function("fuzzy")


def test_keys_reject_non_dict_records():
    with pytest.raises(TypeError, match="must be a dict"):
        keys.exact_key("not a dict")


def test_record_id_is_short_prefix_of_exact_key():
    record = make()

    assert keys.record_id(record) == keys.exact_key(record)[:16]
    assert len(keys.record_id(record)) == 16


def test_near_key_normalizes_www_urls():
    first = make("Security alert", "Visit www.example.com/alert now")
    second = make("Security alert", "Visit www.another-site.org/login now")

    assert keys.near_key(first) == keys.near_key(second)


def test_near_key_does_not_treat_email_domains_as_separate_urls():
    first = make("Contact", "Email help@example.com for support")
    second = make("Contact", "Email help@another.org for support")

    assert keys.near_key(first) == keys.near_key(second)


def test_near_key_normalizes_digit_sequences_consistently():
    first = make("Code 12345", "Reference number 67890")
    second = make("Code 98765", "Reference number 43210")

    assert keys.near_key(first) == keys.near_key(second)


def test_keys_reject_non_string_subject_and_body():
    with pytest.raises(TypeError, match="subject"):
        keys.exact_key(make(subject=123))

    with pytest.raises(TypeError, match="body"):
        keys.near_key(make(body=["not", "text"]))
