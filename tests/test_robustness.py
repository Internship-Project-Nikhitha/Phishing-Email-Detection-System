"""Robustness tests: malformed input, missing fields, duplicates, unusual text (Member 2).

Goal: bad input must produce a clear validation error or a normal result,
never an unexpected crash.
"""

import pytest

from src import ingest, reports, service, storage
from src.preprocessing import EmailValidationError
from tests.helpers import FakePredictor


@pytest.fixture
def conn():
    connection = storage.connect(":memory:")
    yield connection
    connection.close()


def analyze(record, **kwargs):
    return service.analyze_record(record, FakePredictor(), **kwargs)


@pytest.mark.parametrize(
    "record",
    [
        {"subject": "Only a subject"},
        {"body": "Only a body"},
        {"subject": None, "body": "Body", "sender": None},
        {"subject": "S", "body": "B", "sender": ""},
        {"subject": "S", "body": "B", "unexpected_field": [1, 2, 3]},
    ],
)
def test_missing_or_extra_fields_still_give_a_valid_result(record):
    result = analyze(record)

    assert result["label"] in ("phishing", "legitimate")
    assert 0.0 <= result["score"] <= 1.0


@pytest.mark.parametrize(
    "record, message",
    [
        ({}, "no usable content"),
        ({"subject": "", "body": "   \n\t"}, "no usable content"),
        ({"subject": 123, "body": "x"}, "must be a string"),
        ({"subject": "x", "body": ["a"]}, "must be a string"),
        ({"subject": "x", "sender": {"a": 1}}, "must be a string"),
        (None, "must be a dict"),
        ("a string", "must be a dict"),
        (["list"], "must be a dict"),
    ],
)
def test_invalid_records_raise_validation_errors_not_crashes(record, message):
    with pytest.raises(EmailValidationError, match=message):
        analyze(record)


def test_very_long_body_is_handled():
    result = analyze({"subject": "Long", "body": "word " * 200_000})

    assert result["score"] == 0.05


def test_many_links_are_handled_quickly():
    body = " ".join(f"http://host{i}.example.invalid/path?x={i}" for i in range(2000))

    assert analyze({"subject": "Links", "body": body})["score"] == 0.05


@pytest.mark.parametrize(
    "text",
    ["Привет, проверьте пароль", "パスワードを確認してください", "مرحبا بالعالم", "emoji 🎣🔒 test", "null\x00byte and \x1b[31mcontrol", "é combining"],
)
def test_unicode_and_control_characters_are_handled(text):
    result = analyze({"subject": text, "body": text})

    assert result["label"] in ("phishing", "legitimate")


def test_html_only_and_malformed_html_bodies_are_handled():
    for body in ("<html><body><a href='http://x.example.invalid'>y</a></body></html>", "<a href=<<<>>>", "<<<<>>>>", "</a></a></a>"):
        assert analyze({"subject": "s", "body": body})["score"] in (0.05, 0.95)


@pytest.mark.parametrize(
    "sender",
    ["", "no-at-sign", "@", "a@", "@b.com", "<>", "a@b@c.com", "Name <not an address", "a@" + "x" * 500 + ".com", "‮evil@example.com"],
)
def test_odd_sender_values_do_not_crash(sender):
    assert analyze({"subject": "s", "body": "b", "sender": sender})["label"]


def test_duplicate_emails_are_stored_twice_with_the_same_hash(conn):
    record = {"subject": "Verify your password", "body": "now"}

    first = service.analyze_and_store(conn, record, FakePredictor())
    second = service.analyze_and_store(conn, dict(record), FakePredictor())

    assert first["id"] != second["id"]
    assert first["content_sha256"] == second["content_sha256"]
    assert len(storage.list_history(conn)) == 2


def test_unseen_text_gets_a_score_without_errors():
    assert analyze({"subject": "zxqv wplk", "body": "gibberish tokens never seen before"})["score"] == 0.05


@pytest.mark.parametrize(
    "data",
    [b"", b"\x00\x01\x02", b"Subject only no blank line", b"From: a@b.c\r\n\r\n", b"Content-Type: multipart/mixed; boundary=X\r\n\r\n--X\r\n", b"\xff\xfe\xfd"],
)
def test_malformed_eml_bytes_never_crash_with_an_unexpected_error(data):
    try:
        parsed = ingest.parse_eml(data)
    except ingest.IngestError:
        return
    assert set(parsed) >= {"subject", "body", "sender", "attachments"}


def test_eml_without_body_is_rejected_cleanly_at_analysis_time():
    parsed = ingest.parse_eml(b"From: a@example.com\r\nSubject:\r\n\r\n")

    with pytest.raises(EmailValidationError, match="no usable content"):
        analyze({key: parsed[key] for key in ("subject", "body", "sender")})


def test_ragged_and_odd_csv_uploads():
    ragged = b"subject,body,sender\nOnly subject\n,Body only,\n\"quoted, comma\",text,a@example.com\n"

    rows = ingest.parse_csv_upload(ragged)
    results, errors = service.analyze_many(rows, FakePredictor())

    assert len(rows) == 3 and len(results) == 3 and errors == []


def test_exports_survive_hostile_text_in_names(conn):
    result = service.analyze_and_store(conn, {"subject": "x", "body": "y"}, FakePredictor(), source_name='=cmd|"/c calc"!A1|<script>')

    analysis = storage.get_analysis(conn, result["id"])

    assert "'=cmd" in reports.history_to_csv([analysis])
    assert "Phishing analysis report" in reports.analysis_to_markdown(analysis)
    assert reports.analysis_to_json(analysis)


def test_history_is_empty_and_exports_work_on_an_empty_database(conn):
    assert storage.list_history(conn) == []
    assert reports.history_to_csv([]).startswith("id,")
    assert storage.get_analysis(conn, 1) is None
