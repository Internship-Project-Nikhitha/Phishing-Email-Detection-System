"""Configuration and API documentation must agree with the code.

If someone adds a setting or an endpoint and forgets the docs, one of these fails.
"""

import re
from dataclasses import fields
from pathlib import Path

import pytest

from src import settings as settings_module
from src.settings import Settings, load_settings

ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / ".env.example"
API_DOC = ROOT / "docs" / "api.md"
# Environment variable -> Settings field it fills.
ENV_TO_FIELD = {
    "MODEL_DIR": "model_dir",
    "DB_PATH": "db_path",
    "RISK_MEDIUM": "medium_threshold",
    "RISK_HIGH": "high_threshold",
    "DECISION_THRESHOLD": "decision_threshold",
}


def env_example_values() -> dict[str, str]:
    values = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            values[name.strip()] = value.strip()
    return values


def variables_read_by_settings() -> set[str]:
    source = Path(settings_module.__file__).read_text(encoding="utf-8")
    return set(re.findall(r'"([A-Z][A-Z_]{3,})"', source))


def test_env_example_lists_exactly_the_variables_the_code_reads():
    assert set(env_example_values()) == variables_read_by_settings()


def test_the_variable_to_field_table_covers_every_settings_field():
    assert set(ENV_TO_FIELD.values()) == {field.name for field in fields(Settings)}


@pytest.mark.parametrize("variable", sorted(ENV_TO_FIELD))
def test_env_example_default_equals_the_code_default(variable):
    field = ENV_TO_FIELD[variable]
    default = getattr(Settings(), field)
    example = env_example_values()[variable]

    assert example == str(default)


def test_env_example_loads_without_errors():
    loaded = load_settings(env_example_values())

    assert loaded == Settings()


def test_every_variable_sits_in_a_block_with_an_explaining_comment():
    lines = ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() and not line.startswith("#"):
            block = []
            for earlier in reversed(lines[:index]):
                if not earlier.strip():
                    break
                block.append(earlier)
            assert any(text.startswith("#") for text in block), f"{line} has no explaining comment"


def test_env_file_itself_is_ignored_by_git():
    ignored = {line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}

    assert ".env" in ignored


def normalize(path: str) -> str:
    """Path parameter names do not matter: /report/{analysis_id} equals /report/{id}."""
    return re.sub(r"\{[^}]+\}", "{id}", path)


def api_routes() -> list[tuple[str, str]]:
    pytest.importorskip("fastapi")
    from app import api

    routes = []
    for route in api.app.routes:
        path = getattr(route, "path", "")
        if path in ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"):
            continue
        for method in sorted(getattr(route, "methods", set()) - {"HEAD", "OPTIONS"}):
            routes.append((method, normalize(path)))
    return routes


def test_there_are_api_routes_to_check():
    assert len(api_routes()) >= 6


def test_every_api_route_is_documented_in_api_md():
    text = normalize(API_DOC.read_text(encoding="utf-8"))
    missing = [f"{method} {path}" for method, path in api_routes() if f"`{method} {path}`" not in text]

    assert not missing, f"docs/api.md does not list: {missing}"


def test_api_md_does_not_document_routes_that_do_not_exist():
    pytest.importorskip("fastapi")
    real = {f"{method} {path}" for method, path in api_routes()}
    documented = set(re.findall(r"`((?:GET|POST|PUT|DELETE|PATCH) /[^`]*)`", normalize(API_DOC.read_text(encoding="utf-8"))))

    assert documented <= real, f"documented but missing in code: {sorted(documented - real)}"


def test_api_md_mentions_every_error_status_the_api_can_raise():
    source = (ROOT / "app" / "api.py").read_text(encoding="utf-8")
    used = set(re.findall(r"status_code=(\d{3})", source))
    text = API_DOC.read_text(encoding="utf-8")

    assert {code for code in used if f"| {code} |" not in text} == set()
