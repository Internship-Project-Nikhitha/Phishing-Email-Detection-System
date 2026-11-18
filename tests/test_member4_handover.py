"""docs/member4-handover.md may only name files, functions and settings that really exist."""

import importlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "member4-handover.md"
TEXT = DOC.read_text(encoding="utf-8")
DAILY_HEADING = "## Added in the daily tasks"


def main_text() -> str:
    """The page without the daily-task section (those files may not be applied yet)."""
    return TEXT.split(DAILY_HEADING)[0]


def daily_text() -> str:
    return TEXT.split(DAILY_HEADING)[1].split("\n## ")[0]


def backticked(text: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", text)


def ownership_rows() -> list[list[str]]:
    section = main_text().split("## What Member 4 owns")[1].split("## ")[0]
    rows = [line for line in section.splitlines() if line.startswith("|")][2:]
    return [[cell.strip() for cell in row.strip("|").split("|")] for row in rows]


def module_name(path: str) -> str:
    return path.removesuffix(".py").replace("/", ".")


def test_the_page_has_every_section():
    for heading in ("What Member 4 owns", "How the pieces fit", "Re-check in five minutes", "Decisions worth knowing", "Known limits"):
        assert f"## {heading}" in TEXT


def test_ownership_table_has_one_row_per_part():
    assert len(ownership_rows()) == 9


@pytest.mark.parametrize("row", ownership_rows(), ids=lambda row: row[1])
def test_owned_file_and_its_test_file_exist(row):
    for cell in (row[1], row[3]):
        for path in backticked(cell):
            assert (ROOT / path).is_file(), f"{path} does not exist"


FUNCTION_ROWS = [r for r in ownership_rows() if backticked(r[1])[0].endswith(".py") and "`" in r[2]]


def test_most_rows_name_functions_so_the_check_below_is_not_empty():
    assert len(FUNCTION_ROWS) >= 7


@pytest.mark.parametrize("row", FUNCTION_ROWS, ids=lambda row: row[1])
def test_named_functions_exist_in_the_owned_module(row):
    name = module_name(backticked(row[1])[0])
    if name.startswith("app."):
        pytest.importorskip("fastapi")
    module = importlib.import_module(name)
    for name in backticked(row[2]):
        assert callable(getattr(module, name, None)), f"{module.__name__}.{name} does not exist"


def test_every_path_mentioned_outside_the_daily_section_exists():
    for token in backticked(main_text()):
        if re.fullmatch(r"[\w./-]+\.(py|md|json|txt)", token) and "/" in token:
            assert (ROOT / token).exists(), f"{token} is mentioned but does not exist"


def test_environment_variables_named_in_the_page_are_real_settings():
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    for token in backticked(main_text()):
        if re.fullmatch(r"[A-Z][A-Z_]{4,}", token):
            assert f"{token}=" in env_example, f"{token} is not in .env.example"


def test_documented_default_thresholds_match_the_code():
    from src.settings import Settings

    defaults = Settings()

    assert (defaults.decision_threshold, defaults.medium_threshold, defaults.high_threshold) == (0.5, 0.4, 0.7)
    assert "default 0.5" in TEXT and "0.4 and 0.7" in TEXT


def test_the_daily_table_lists_six_days_with_distinct_test_files():
    files = [token for token in backticked(daily_text()) if token.startswith("tests/")]

    assert len(files) == 6 and len(set(files)) == 6


def test_daily_files_that_are_present_follow_the_test_naming_rule():
    for token in backticked(daily_text()):
        if token.startswith("tests/") and (ROOT / token).exists():
            assert Path(token).name.startswith("test_")


def test_page_contains_no_unfilled_markers_or_personal_data():
    assert "<FILL" not in TEXT and "TODO" not in TEXT
    assert not re.search(r"[\w.]+@[\w.]+\.\w+", TEXT)
