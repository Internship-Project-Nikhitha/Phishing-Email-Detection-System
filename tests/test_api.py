"""Tests for app/api.py. Skipped automatically unless fastapi and httpx are installed."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app import api  # noqa: E402
from src.settings import Settings  # noqa: E402
from tests.helpers import FakePredictor  # noqa: E402

EML = (
    b"From: a@example.com\r\nSubject: Verify your password\r\nContent-Type: text/plain\r\n\r\n"
    b"Please verify at http://evil.example.invalid/login\r\n"
)


@pytest.fixture
def client(tmp_path):
    settings = Settings(db_path=str(tmp_path / "history.db"))
    api.app.dependency_overrides[api.get_settings] = lambda: settings
    api.app.dependency_overrides[api.get_predictor] = lambda: FakePredictor()
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_analyze_json_stores_and_returns_a_result(client):
    response = client.post("/analyze", json={"subject": "Verify your password", "body": "now", "sender": ""})

    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "phishing" and data["id"] == 1
    assert client.get("/history").json()[0]["id"] == 1


def test_analyze_rejects_empty_emails(client):
    assert client.post("/analyze", json={"subject": "", "body": ""}).status_code == 422


def test_upload_eml_and_download_reports(client):
    response = client.post("/analyze/upload", files={"file": ("mail.eml", EML, "message/rfc822")})

    assert response.status_code == 200
    analysis_id = response.json()["id"]
    assert "Phishing analysis report" in client.get(f"/report/{analysis_id}").text
    assert client.get(f"/report/{analysis_id}?format=json").json()["id"] == analysis_id
    assert client.get("/report/999").status_code == 404
    assert client.get(f"/report/{analysis_id}?format=pdf").status_code == 422


def test_upload_csv_reports_good_and_bad_rows(client):
    data = b"subject,body\nVerify your password,now\n,\n"

    response = client.post("/analyze/upload", files={"file": ("batch.csv", data, "text/csv")})

    body = response.json()
    assert len(body["results"]) == 1 and len(body["errors"]) == 1


@pytest.mark.parametrize("name", ["malware.exe", "../x.eml", "noext"])
def test_upload_rejects_unsafe_files(client, name):
    response = client.post("/analyze/upload", files={"file": (name, b"data", "application/octet-stream")})

    assert response.status_code == 422


def test_history_csv_download(client):
    client.post("/analyze", json={"subject": "Hello", "body": "World"})

    assert client.get("/history.csv").text.startswith("id,created_at")
