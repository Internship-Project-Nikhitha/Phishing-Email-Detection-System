"""Checks that the demo samples in samples/ parse and behave as documented."""

from pathlib import Path

from src import ingest, service
from src.features import pipeline
from tests.helpers import FakePredictor

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def parse(name):
    return ingest.parse_eml((SAMPLES / name).read_bytes())


def test_phishing_sample_shows_the_expected_indicators():
    parsed = parse("phishing_sample.eml")
    record = {key: parsed[key] for key in ("subject", "body", "sender")}

    features = pipeline.extract_all(record)

    assert features["url_anchor_mismatch"] == 1.0
    assert features["sender_suspicious_tld"] == 1.0
    assert features["text_urgent_words"] >= 2.0
    assert features["text_credential_words"] >= 2.0
    assert features["url_plain_http"] == 1.0


def test_legitimate_sample_triggers_almost_nothing():
    parsed = parse("legitimate_sample.eml")
    record = {key: parsed[key] for key in ("subject", "body", "sender")}

    features = pipeline.extract_all(record)

    assert features["url_count"] == 0.0
    assert features["sender_suspicious_tld"] == 0.0
    assert features["text_urgent_words"] == 0.0


def test_attachment_sample_lists_the_attachment_and_warns():
    parsed = parse("suspicious_attachment_sample.eml")

    assert [a["filename"] for a in parsed["attachments"]] == ["invoice.pdf.exe"]
    assert "invoice.pdf.exe" in parsed["attachment_warnings"][0]


def test_batch_csv_has_one_unusable_row_reported_as_an_error():
    rows = ingest.parse_csv_upload((SAMPLES / "sample_batch.csv").read_bytes())

    results, errors = service.analyze_many(rows, FakePredictor())

    assert len(rows) == 4
    assert len(results) == 3 and len(errors) == 1
    assert errors[0]["index"] == 3
