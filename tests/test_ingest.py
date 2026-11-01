"""Tests for src/ingest.py."""

import pytest

from src import ingest as ig


@pytest.mark.parametrize("name, ext", [("mail.eml", ".eml"), ("DATA.CSV", ".csv"), ("a.b.eml", ".eml")])
def test_validate_upload_accepts_allowed_types(name, ext):
    assert ig.validate_upload(name, 100) == ext


@pytest.mark.parametrize(
    "name, size, message",
    [
        ("", 10, "no file name"),
        (None, 10, "no file name"),
        ("../evil.eml", 10, "folders"),
        ("dir/mail.eml", 10, "folders"),
        ("dir\\mail.eml", 10, "folders"),
        ("mail.eml\x00.exe", 10, "folders"),
        ("malware.exe", 10, "Unsupported file type .exe"),
        ("noextension", 10, r"Unsupported file type \(none\)"),
        ("mail.eml", 0, "empty"),
        ("mail.eml", -5, "empty"),
        ("mail.eml", ig.MAX_UPLOAD_BYTES + 1, "too large"),
    ],
)
def test_validate_upload_rejects_unsafe_uploads(name, size, message):
    with pytest.raises(ig.IngestError, match=message):
        ig.validate_upload(name, size)


def test_size_limit_boundary_is_inclusive():
    assert ig.validate_upload("mail.eml", ig.MAX_UPLOAD_BYTES) == ".eml"


# @@PART 2
PLAIN_EML = (
    b"From: Alice Example <alice@example.com>\r\n"
    b"To: bob@example.com\r\n"
    b"Subject: Weekly notes\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
    b"Hello Bob,\r\nsee http://notes.example.invalid/today for details.\r\n"
)

ATTACHMENT_EML = (
    b"From: Billing <billing@example.invalid>\r\n"
    b"Subject: Invoice attached\r\n"
    b"MIME-Version: 1.0\r\n"
    b'Content-Type: multipart/mixed; boundary="XX"\r\n\r\n'
    b"--XX\r\nContent-Type: text/plain\r\n\r\nPlease open the attachment.\r\n"
    b"--XX\r\nContent-Type: application/octet-stream\r\n"
    b'Content-Disposition: attachment; filename="../../invoice.pdf.exe"\r\n'
    b"Content-Transfer-Encoding: base64\r\n\r\nbm90IGEgcmVhbCBwcm9ncmFt\r\n"
    b"--XX--\r\n"
)

HTML_ONLY_EML = (
    b"From: news@example.com\r\nSubject: Offer\r\nContent-Type: text/html\r\n\r\n"
    b'<html><body><a href="http://evil.example.invalid">www.good.example.com</a></body></html>\r\n'
)


def test_parse_eml_plain_message():
    parsed = ig.parse_eml(PLAIN_EML)

    assert parsed["subject"] == "Weekly notes"
    assert parsed["sender"] == "Alice Example <alice@example.com>"
    assert "http://notes.example.invalid/today" in parsed["body"]
    assert parsed["attachments"] == []
    assert parsed["attachment_warnings"] == []


def test_parse_eml_lists_attachments_without_returning_their_content():
    parsed = ig.parse_eml(ATTACHMENT_EML)

    assert parsed["body"].strip() == "Please open the attachment."
    assert parsed["attachments"] == [
        {"filename": "invoice.pdf.exe", "content_type": "application/octet-stream", "size": 18}
    ]
    assert "bm90IGEgcmVhbCBwcm9ncmFt" not in str(parsed)
    assert "not a real program" not in str(parsed)


def test_risky_attachments_produce_a_warning():
    parsed = ig.parse_eml(ATTACHMENT_EML)

    assert len(parsed["attachment_warnings"]) == 1
    assert "invoice.pdf.exe" in parsed["attachment_warnings"][0]
    assert ig.attachment_warnings([{"filename": "report.pdf"}, {"filename": "x.DOCM"}]) == [
        "Attachment 'x.DOCM' has a potentially executable or macro-enabled type (.docm). Do not open it."
    ]


def test_html_only_message_keeps_the_html_source_for_link_analysis():
    parsed = ig.parse_eml(HTML_ONLY_EML)

    assert '<a href="http://evil.example.invalid">' in parsed["body"]


def test_parse_eml_handles_missing_headers_and_garbage():
    parsed = ig.parse_eml(b"\r\nJust a body with no headers")

    assert parsed["subject"] == ""
    assert parsed["sender"] == ""
    assert "Just a body" in parsed["body"]
    assert ig.parse_eml(b"\x00\x01\x02 not an email") is not None


def test_parse_eml_rejects_wrong_types_and_oversize_data():
    with pytest.raises(ig.IngestError, match="must be bytes"):
        ig.parse_eml("text, not bytes")
    with pytest.raises(ig.IngestError, match="too large"):
        ig.parse_eml(b"x" * (ig.MAX_UPLOAD_BYTES + 1))


# @@PART 3
def test_parse_csv_upload_reads_rows_with_flexible_headers():
    data = b"Subject,BODY,Sender,Label\nHi,Hello there,a@example.com,phishing\nBye,See you,,legitimate\n"

    rows = ig.parse_csv_upload(data)

    assert rows == [
        {"subject": "Hi", "body": "Hello there", "sender": "a@example.com"},
        {"subject": "Bye", "body": "See you", "sender": ""},
    ]


def test_parse_csv_upload_accepts_body_only_and_utf8_bom():
    rows = ig.parse_csv_upload("﻿body\nonly body\n".encode("utf-8"))

    assert rows == [{"subject": "", "body": "only body", "sender": ""}]


@pytest.mark.parametrize(
    "data, message",
    [
        (b"sender,label\na@example.com,x\n", "'subject' and/or 'body'"),
        (b"subject,body\n", "no rows"),
        (b"", "'subject' and/or 'body'"),
        (b"\xff\xfe\x00bad", "UTF-8"),
        ("text", "must be bytes"),
    ],
)
def test_parse_csv_upload_rejects_bad_files(data, message):
    with pytest.raises(ig.IngestError, match=message):
        ig.parse_csv_upload(data)


def test_parse_csv_upload_enforces_the_row_limit():
    rows = "".join(f"s{i},b{i}\n" for i in range(ig.MAX_CSV_ROWS + 1))

    with pytest.raises(ig.IngestError, match="more than"):
        ig.parse_csv_upload(("subject,body\n" + rows).encode())

    ok = "".join(f"s{i},b{i}\n" for i in range(ig.MAX_CSV_ROWS))
    assert len(ig.parse_csv_upload(("subject,body\n" + ok).encode())) == ig.MAX_CSV_ROWS


def test_formula_like_cells_are_kept_as_plain_text():
    rows = ig.parse_csv_upload(b'subject,body\n"=1+1","@SUM(A1)"\n')

    assert rows[0]["subject"] == "=1+1"
