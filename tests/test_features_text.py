"""Tests for src/features/text.py."""

import pytest

from src.features import text as tf


def feats(body, subject=""):
    return tf.extract({"subject": subject, "body": body})


def test_count_phrases_matches_whole_words_only():
    assert tf.count_phrases("Act now! ACT NOW.", ("act now",)) == 2
    assert tf.count_phrases("a pinch of salt", ("pin",)) == 0
    assert tf.count_phrases("enter your PIN", ("pin",)) == 1
    assert tf.count_phrases("", ("pin",)) == 0


def test_length_and_word_count():
    result = feats("one two three four", subject="Hello")

    assert result["text_subject_length"] == 5.0
    assert result["text_body_words"] == 4.0


def test_exclamations_and_uppercase_ratio():
    result = feats("WIN!!", subject="ok")

    assert result["text_exclamations"] == 2.0
    # letters: o k W I N -> 3 of 5 are capitals
    assert result["text_uppercase_ratio"] == pytest.approx(3 / 5)


def test_uppercase_ratio_with_no_letters_is_zero():
    assert feats("12345 !!!")["text_uppercase_ratio"] == 0.0


def test_urgent_words_are_counted():
    result = feats("Urgent: your account is suspended. Act now to avoid closure.")

    assert result["text_urgent_words"] == 3.0  # urgent, suspended, act now


# @@PART 2
def test_credential_and_money_words():
    result = feats("Please verify your password and confirm the payment of your prize.")

    assert result["text_credential_words"] == 3.0  # verify, password, confirm
    assert result["text_money_words"] == 2.0  # payment, prize


def test_html_and_form_detection():
    assert feats("<p>hello</p>")["text_has_html"] == 0.0  # plain <p> is not counted
    assert feats('<div>hi <a href="x">y</a></div>')["text_has_html"] == 1.0
    assert feats('<form action="x"><input name="password"></form>')["text_has_form"] == 1.0
    assert feats("no markup")["text_has_form"] == 0.0


def test_fake_reply_prefix():
    assert tf.extract({"subject": "RE: your invoice", "body": ""})["text_fake_reply_prefix"] == 1.0
    assert tf.extract({"subject": "Fwd: hello", "body": ""})["text_fake_reply_prefix"] == 1.0
    assert tf.extract({"subject": "Regarding your invoice", "body": ""})["text_fake_reply_prefix"] == 0.0


def test_digit_ratio():
    assert tf.extract({"subject": "ab", "body": "12"})["text_digit_ratio"] == pytest.approx(0.5)
    assert tf.extract({})["text_digit_ratio"] == 0.0


def test_empty_record_gives_all_zero_features():
    assert set(tf.extract({}).values()) == {0.0}


def test_every_feature_has_a_description_and_the_text_prefix():
    result = feats("hello")

    assert set(result) == set(tf.descriptions())
    assert all(name.startswith("text_") for name in result)
