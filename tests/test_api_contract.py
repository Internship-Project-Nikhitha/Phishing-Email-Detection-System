"""API contract: paging, error codes, configuration failures and privacy of the stored history.

Skipped automatically unless fastapi and httpx are installed (same rule as test_api.py).
"""

import sqlite3

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app import api  # noqa: E402
from src import ingest  # noqa: E402
from src.settings import Settings  # noqa: E402
from tests.helpers import FakePredictor  # noqa: E402

SECRET_BODY = "UniqueSecretBodyText please verify the account"


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "history.db")


@pytest.fixture
def client(db_path):
    settings = Settings(db_path=db_path)
    api.app.dependency_overrides[api.get_settings] = lambda: settings
    api.app.dependency_overrides[api.get_predictor] = lambda: FakePredictor()
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def post_many(client, count):
    for number in range(count):
        assert client.post("/analyze", json={"subject": f"Mail {number}", "body": "hello"}).status_code == 200


def test_history_pages_are_newest_first_and_do_not_overlap(client):
    post_many(client, 5)

    first = client.get("/history?limit=2&offset=0").json()
    second = client.get("/history?limit=2&offset=2").json()
    last = client.get("/history?limit=2&offset=4").json()

    assert [row["id"] for row in first] == [5, 4]
    assert [row["id"] for row in second] == [3, 2]
    assert [row["id"] for row in last] == [1]


def test_history_is_an_empty_list_before_any_analysis(client):
    assert client.get("/history").json() == []


@pytest.mark.parametrize("query", ["limit=0", "limit=1001", "offset=-1"])
def test_history_rejects_out_of_range_paging(client, query):
    assert client.get(f"/history?{query}").status_code == 422


@pytest.mark.parametrize("query", ["limit=abc", "offset=x"])
def test_history_rejects_non_numeric_paging(client, query):
    assert client.get(f"/history?{query}").status_code == 422


def test_report_id_must_be_a_number(client):
    assert client.get("/report/abc").status_code == 422


@pytest.mark.parametrize(
    "payload",
    [{"subject": 5, "body": "x"}, {"subject": "x", "body": ["a"]}, {"subject": "x", "sender": {"a": 1}}],
)
def test_analyze_rejects_wrong_field_types(client, payload):
    assert client.post("/analyze", json=payload).status_code == 422


def test_analyze_rejects_a_non_json_body(client):
    assert client.post("/analyze", content=b"not json", headers={"content-type": "application/json"}).status_code == 422


def test_analyze_accepts_a_sender_only_when_there_is_text(client):
    assert client.post("/analyze", json={"sender": "a@example.com"}).status_code == 422
    assert client.post("/analyze", json={"sender": "a@example.com", "subject": "Hi"}).status_code == 200


def test_upload_without_a_file_part_is_rejected(client):
    assert client.post("/analyze/upload").status_code == 422


def test_empty_upload_is_rejected(client):
    response = client.post("/analyze/upload", files={"file": ("mail.eml", b"", "message/rfc822")})

    assert response.status_code == 422


def test_oversize_upload_is_rejected_before_parsing(client):
    big = b"a" * (ingest.MAX_UPLOAD_BYTES + 10)

    response = client.post("/analyze/upload", files={"file": ("big.csv", big, "text/csv")})

    assert response.status_code == 422
    assert "too large" in response.json()["detail"].lower()


def test_csv_with_too_many_rows_is_rejected(client):
    rows = "\n".join(f"Subject {n},body" for n in range(ingest.MAX_CSV_ROWS + 1))

    response = client.post("/analyze/upload", files={"file": ("many.csv", f"subject,body\n{rows}\n".encode(), "text/csv")})

    assert response.status_code == 422


def test_risky_attachment_warning_reaches_the_response(client):
    eml = (
        b"From: a@example.com\r\nSubject: Invoice\r\nMIME-Version: 1.0\r\n"
        b'Content-Type: multipart/mixed; boundary="b"\r\n\r\n'
        b"--b\r\nContent-Type: text/plain\r\n\r\nSee attached\r\n"
        b'--b\r\nContent-Type: application/octet-stream\r\nContent-Disposition: attachment; filename="invoice.exe"\r\n\r\nMZ\r\n--b--\r\n'
    )

    data = client.post("/analyze/upload", files={"file": ("m.eml", eml, "message/rfc822")}).json()

    assert any("invoice.exe" in warning for warning in data["warnings"])
    assert "MZ" not in str(data)


def test_stored_history_never_contains_the_email_text(client, db_path):
    client.post("/analyze", json={"subject": "Subject line", "body": SECRET_BODY, "sender": "who@example.com"})

    conn = sqlite3.connect(db_path)
    try:
        dump = "\n".join(str(row) for row in conn.execute("SELECT * FROM analysis_history"))
    finally:
        conn.close()
    assert SECRET_BODY not in dump and "who@example.com" not in dump
    assert SECRET_BODY not in client.get("/history.csv").text
    assert SECRET_BODY not in client.get("/report/1").text


def test_history_csv_has_one_line_per_analysis_plus_header(client):
    post_many(client, 3)

    lines = client.get("/history.csv").text.strip().splitlines()

    assert len(lines) == 4


def test_missing_model_gives_503_with_a_helpful_message(db_path, monkeypatch, tmp_path):
    api._cache.clear()
    api.app.dependency_overrides[api.get_settings] = lambda: Settings(db_path=db_path, model_dir=str(tmp_path / "no-model"))
    try:
        response = TestClient(api.app).post("/analyze", json={"subject": "Hi", "body": "there"})
    finally:
        api.app.dependency_overrides.clear()
        api._cache.clear()

    assert response.status_code == 503
    assert "train" in response.json()["detail"].lower()


def test_bad_environment_settings_give_500(monkeypatch):
    monkeypatch.setenv("RISK_MEDIUM", "not-a-number")
    api.app.dependency_overrides[api.get_predictor] = lambda: FakePredictor()
    try:
        response = TestClient(api.app).post("/analyze", json={"subject": "Hi", "body": "there"})
    finally:
        api.app.dependency_overrides.clear()

    assert response.status_code == 500
    assert "RISK_MEDIUM" in response.json()["detail"]


def test_custom_thresholds_from_settings_change_the_risk_level(db_path):
    settings = Settings(db_path=db_path, medium_threshold=0.01, high_threshold=0.02)
    api.app.dependency_overrides[api.get_settings] = lambda: settings
    api.app.dependency_overrides[api.get_predictor] = lambda: FakePredictor(score=0.05)
    try:
        data = TestClient(api.app).post("/analyze", json={"subject": "Hi", "body": "there"}).json()
    finally:
        api.app.dependency_overrides.clear()

    assert data["risk_level"] == "high"
