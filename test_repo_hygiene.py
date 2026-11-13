"""Files that must never be committed: secrets, raw data, trained models and local databases."""

import fnmatch
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = [
    ".env",
    "*.joblib",
    "*.db",
    "*.sqlite3",
    "data/raw/*",
    "data/processed/*",
    "reports/split_ids.csv",
]
MUST_BE_IGNORED = [".env", "data/raw/", "data/processed/", "models/**/*.joblib", "*.db", "reports/split_ids.csv"]


def tracked_files() -> list[str]:
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.splitlines()


def test_no_forbidden_file_is_tracked():
    bad = [
        name
        for name in tracked_files()
        if any(fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(Path(name).name, pattern) for pattern in FORBIDDEN)
    ]
    assert not bad, f"These files must not be committed: {bad}"


def test_gitignore_lists_every_protected_path():
    lines = {line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}
    missing = [entry for entry in MUST_BE_IGNORED if entry not in lines]
    assert not missing, f".gitignore is missing: {missing}"


def test_env_example_has_no_real_secret():
    text = (ROOT / ".env.example").read_text(encoding="utf-8").lower()
    for word in ("password=", "api_key=", "secret=", "token="):
        assert word not in text
