"""Safety tests (Member 3): the code must never visit links or run attachments.

Two kinds of checks:

1. STATIC: no file in src/, app/ or scripts/ imports network, process-launching
   or dynamic-execution modules (scanned with Python's ``ast`` module).
2. RUNTIME: analyzing emails full of links and an executable attachment makes no
   network call and writes no files.
"""

import ast
import http.client
import socket
import urllib.request
from pathlib import Path

import pytest

from src import ingest, service
from tests.helpers import FakePredictor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCANNED_FOLDERS = ("src", "app", "scripts")
SAMPLES = PROJECT_ROOT / "samples"

FORBIDDEN_MODULES = {
    "requests", "httpx", "aiohttp", "urllib3", "urllib.request", "http.client", "socket", "ftplib",
    "smtplib", "imaplib", "poplib", "telnetlib", "webbrowser", "subprocess", "pickle", "ctypes",
}
FORBIDDEN_CALLS = {"eval", "exec", "__import__", "compile", "os.system", "os.popen", "os.startfile"}


def python_files():
    for folder in SCANNED_FOLDERS:
        yield from sorted((PROJECT_ROOT / folder).rglob("*.py"))


def imported_modules(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module
            for alias in node.names:
                yield f"{node.module}.{alias.name}"


def called_names(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                yield node.func.id
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                yield f"{node.func.value.id}.{node.func.attr}"


def test_there_are_files_to_scan():
    assert len(list(python_files())) >= 10


@pytest.mark.parametrize("path", list(python_files()), ids=lambda p: p.relative_to(PROJECT_ROOT).as_posix())
def test_no_forbidden_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    bad = [name for name in imported_modules(tree) if name in FORBIDDEN_MODULES or name.split(".")[0] in {"requests", "httpx", "aiohttp", "urllib3", "socket", "subprocess", "pickle"}]

    assert bad == [], f"{path.name} imports forbidden modules: {bad}"


@pytest.mark.parametrize("path", list(python_files()), ids=lambda p: p.relative_to(PROJECT_ROOT).as_posix())
def test_no_dynamic_execution_calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    bad = sorted(set(called_names(tree)) & FORBIDDEN_CALLS)

    assert bad == [], f"{path.name} calls forbidden functions: {bad}"


def test_the_static_scan_really_detects_a_violation():
    tree = ast.parse("import requests\nfrom urllib.request import urlopen\nexec('1')\nos.system('x')\nre.compile('ok')")

    assert "requests" in set(imported_modules(tree))
    assert "urllib.request" in set(imported_modules(tree))
    assert {"exec", "os.system"} <= set(called_names(tree))
    assert "re.compile" not in FORBIDDEN_CALLS  # regex compile is fine; only the bare builtin is forbidden


@pytest.fixture
def no_network(monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError("Network access attempted.")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(http.client.HTTPConnection, "request", forbidden)
    return calls


@pytest.mark.parametrize("name", ["phishing_sample.eml", "legitimate_sample.eml", "suspicious_attachment_sample.eml"])
def test_analyzing_samples_makes_no_network_calls_and_writes_no_files(name, no_network, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = sorted(p.name for p in tmp_path.iterdir())

    parsed = ingest.parse_eml((SAMPLES / name).read_bytes())
    record = {key: parsed[key] for key in ("subject", "body", "sender")}
    result = service.analyze_record(record, FakePredictor(), extra_warnings=parsed["attachment_warnings"])

    assert result["label"] in ("phishing", "legitimate")
    assert no_network == []
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_attachment_content_is_never_returned_or_stored():
    parsed = ingest.parse_eml((SAMPLES / "suspicious_attachment_sample.eml").read_bytes())

    assert set(parsed["attachments"][0]) == {"filename", "content_type", "size"}
    assert "harmless placeholder" not in str(parsed)


def test_urls_in_email_text_stay_plain_text(no_network):
    url = "http://login.example.invalid/verify?token=abc"
    record = {"subject": "Link", "body": f"Open {url} now"}

    result = service.analyze_record(record, FakePredictor())

    assert no_network == []
    assert url not in str(result)  # results never echo email content


def test_unsafe_upload_names_and_types_are_rejected_before_parsing():
    for name in ("run.exe", "../../etc/passwd.eml", "script.js", "archive.zip"):
        with pytest.raises(ingest.IngestError):
            ingest.validate_upload(name, 100)
