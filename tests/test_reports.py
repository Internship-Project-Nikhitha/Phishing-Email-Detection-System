"""Tests for src/reports.py."""

import csv
import io
import json

import pytest

from src import reports as rp

ANALYSIS = {
    "id": 7,
    "created_at": "2026-11-02T09:30:00+00:00",
    "source_name": "mail.eml",
    "content_sha256": "a" * 64,
    "label": "phishing",
    "score": 0.91,
    "risk_level": "high",
    "model_version": "v1",
    "indicators": [{"feature": "url_count", "description": "Number | of links", "contribution": 0.5, "value": 2.0}],
    "warnings": ["Attachment 'a.exe' looks executable."],
}


@pytest.mark.parametrize(
    "value, expected",
    [("=SUM(A1)", "'=SUM(A1)"), ("+1", "'+1"), ("-1", "'-1"), ("@x", "'@x"), ("normal", "normal"), (None, ""), (5, "5")],
)
def test_sanitize_csv_cell(value, expected):
    assert rp.sanitize_csv_cell(value) == expected


def test_analysis_to_json_round_trips():
    assert json.loads(rp.analysis_to_json(ANALYSIS)) == ANALYSIS


def test_markdown_report_contains_result_indicators_and_disclaimer():
    text = rp.analysis_to_markdown(ANALYSIS)

    assert text.startswith("# Phishing analysis report #7")
    assert "**Risk level:** high" in text
    assert "Number \\| of links" in text  # pipes are escaped so the table stays intact
    assert "Attachment 'a.exe' looks executable." in text
    assert "Links in the email were not opened" in text


def test_markdown_report_without_indicators():
    text = rp.analysis_to_markdown({**ANALYSIS, "indicators": [], "warnings": []})

    assert "No indicators pointed toward phishing." in text
    assert "## Warnings" not in text


def test_history_csv_has_header_rows_and_neutralizes_formulas():
    rows = [ANALYSIS, {**ANALYSIS, "id": 8, "source_name": "=HYPERLINK(\"http://x.example.invalid\")"}]

    parsed = list(csv.reader(io.StringIO(rp.history_to_csv(rows))))

    assert tuple(parsed[0]) == rp.CSV_COLUMNS
    assert parsed[1][0] == "7"
    assert parsed[2][2].startswith("'=HYPERLINK")


def test_history_csv_never_contains_indicator_or_email_text():
    text = rp.history_to_csv([ANALYSIS])

    assert "Number" not in text
    assert "url_count" not in text


def test_history_csv_with_no_rows_is_just_a_header():
    assert rp.history_to_csv([]).strip() == ",".join(rp.CSV_COLUMNS)
