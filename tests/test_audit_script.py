"""Tests for scripts/audit_dataset.py."""

from pathlib import Path

from scripts import audit_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT_ROOT / "tests" / "fixtures" / "sample_dataset.json"


def test_build_report_has_the_expected_numbers_for_the_fixture():
    report = audit_dataset.build_report(CONFIG, base_dir=PROJECT_ROOT)

    assert "Data rows read: **58**" in report
    assert "Valid records: **55**" in report
    assert "Rejected rows: **3**" in report
    assert "| unknown label | 1 |" in report
    assert "| phishing | 29 | 52.73% |" in report
    assert "| legitimate | 26 | 47.27% |" in report
    assert "Records kept: **48**" in report
    assert "Duplicates removed: **5**" in report


def test_report_contains_no_email_text():
    report = audit_dataset.build_report(CONFIG, base_dir=PROJECT_ROOT)

    assert "password" not in report
    assert "example.invalid" not in report


def test_main_writes_the_report_file(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    out = tmp_path / "reports" / "audit.md"

    code = audit_dataset.main(["--config", str(CONFIG), "--out", str(out)])

    assert code == 0
    assert out.read_text(encoding="utf-8").startswith("# Dataset audit report")


def test_main_reports_config_errors_without_a_traceback(tmp_path, capsys):
    code = audit_dataset.main(["--config", str(tmp_path / "missing.json"), "--out", str(tmp_path / "o.md")])

    assert code == 1
    assert "Config file not found" in capsys.readouterr().err
