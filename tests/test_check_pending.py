"""Tests for the scoped dataset pending-marker checker."""

from io import StringIO
from pathlib import Path

from scripts.check_pending import DEFAULT_PATHS, check_pending


def test_clean_file_reports_no_markers_and_succeeds(tmp_path: Path):
    path = tmp_path / "clean.md"
    path.write_text("Dataset review is complete.\n", encoding="utf-8")
    output = StringIO()

    result = check_pending([path], output)

    assert result == 0
    assert output.getvalue() == "No pending markers found in the configured dataset files.\n"


def test_pending_markers_are_reported_without_failing(tmp_path: Path):
    path = tmp_path / "selection.md"
    path.write_text(
        "Status: PENDING\nColumn mapping: <FILL this after selection>\nUNVERIFIED source\n",
        encoding="utf-8",
    )
    output = StringIO()

    result = check_pending([path], output)

    report = output.getvalue()
    assert result == 0
    assert "selection.md:1: unresolved marker 'PENDING'" in report
    assert "selection.md:2: unresolved marker '<FILL this after selection>'" in report
    assert "selection.md:3: unresolved marker 'UNVERIFIED'" in report
    assert "informational" in report


def test_missing_path_is_reported_as_a_checker_error(tmp_path: Path):
    output = StringIO()

    result = check_pending([tmp_path / "missing.md"], output)

    assert result == 2
    assert "ERROR: cannot read" in output.getvalue()
    assert "Could not inspect 1 required file(s)." in output.getvalue()


def test_default_dataset_paths_report_intentional_pending_items():
    output = StringIO()

    result = check_pending(DEFAULT_PATHS, output)

    assert result == 0
    assert "unresolved marker 'PENDING'" in output.getvalue()
    assert "informational" in output.getvalue()
