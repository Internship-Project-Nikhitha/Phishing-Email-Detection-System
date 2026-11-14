"""Every relative link in the Markdown documentation must point to a file that exists."""

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", ".venv312", "venv", "node_modules", "__pycache__", ".pytest_cache"}
LINK = re.compile(r"\]\(([^)\s]+)\)")


def markdown_files() -> list[Path]:
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        found.extend(Path(folder, name) for name in files if name.endswith(".md"))
    return sorted(found)


def relative_targets(text: str) -> list[str]:
    targets = []
    for match in LINK.finditer(text):
        target = match.group(1).split("#", 1)[0]
        if target and not target.startswith(("http://", "https://", "mailto:")):
            targets.append(target)
    return targets


def test_helper_ignores_web_links_and_fragments():
    text = "[a](https://example.com) [b](#top) [c](docs/x.md#part) [d](mailto:a@b.c)"
    assert relative_targets(text) == ["docs/x.md"]


def test_repository_has_markdown_files():
    names = {path.name for path in markdown_files()}
    assert {"README.md", "dataset-card.md", "limitations.md"} <= names


@pytest.mark.parametrize("path", markdown_files(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_relative_links_exist(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    missing = [t for t in relative_targets(text) if not (path.parent / t).exists()]
    assert not missing, f"{path.relative_to(ROOT).as_posix()} links to missing files: {missing}"
