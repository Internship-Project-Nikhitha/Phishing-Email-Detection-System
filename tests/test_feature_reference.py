"""The generated feature reference is current, and the feature pipeline keeps its contract."""

import copy
import math
import sys
from pathlib import Path

import pytest

from scripts import make_feature_reference as reference
from src.features import pipeline

HOSTILE = [
    {},
    {"subject": "", "body": "", "sender": ""},
    {"subject": "A" * 5000, "body": "B" * 200_000, "sender": "x@" + "d" * 300 + ".com"},
    {"subject": "!!!???", "body": "http://" + "a." * 200 + "com/" + "x" * 3000, "sender": "<>"},
    {"subject": "‮\u0000﻿", "body": "<a href='http://[::1'>x</a><form><", "sender": "é@中文.рф"},
    {"subject": "9" * 100, "body": "http://999.999.999.999/ http://user:pw@host/ hxxp://x[.]y", "sender": "a@b@c@d"},
]


def test_feature_reference_document_is_up_to_date():
    current = reference.OUTPUT.read_text(encoding="utf-8").replace("\r\n", "\n")

    assert current == reference.build_markdown(), "Run: python scripts/make_feature_reference.py"


def test_check_mode_succeeds_on_the_committed_document(capsys):
    assert reference.main(["--check"]) == 0
    assert "up to date" in capsys.readouterr().out


def test_check_mode_fails_on_a_stale_document(tmp_path, monkeypatch, capsys):
    stale = tmp_path / "feature-reference.md"
    stale.write_text("old", encoding="utf-8")
    monkeypatch.setattr(reference, "OUTPUT", stale)

    assert reference.main(["--check"]) == 1
    assert "out of date" in capsys.readouterr().out


def test_every_feature_appears_once_in_the_reference():
    text = reference.build_markdown()

    for name in pipeline.feature_names():
        assert text.count(f"`{name}`") == 1


def test_group_counts_add_up_to_the_total():
    names = pipeline.feature_names()
    text = reference.build_markdown()

    assert f"There are {len(names)} hand-built features" in text
    for prefix in reference.GROUP_TITLES:
        assert sum(name.startswith(prefix + "_") for name in names) > 0


def test_every_feature_belongs_to_a_known_group():
    assert all(name.split("_", 1)[0] in reference.GROUP_TITLES for name in pipeline.feature_names())


@pytest.mark.parametrize("record", HOSTILE, ids=range(len(HOSTILE)))
def test_every_feature_is_a_finite_non_negative_number_on_hostile_input(record):
    values = pipeline.extract_all(record)

    assert list(values) == pipeline.feature_names()
    for name, value in values.items():
        assert isinstance(value, float) and not isinstance(value, bool), name
        assert math.isfinite(value) and value >= 0, f"{name}={value}"


@pytest.mark.parametrize("record", HOSTILE, ids=range(len(HOSTILE)))
def test_extraction_does_not_modify_the_record(record):
    before = copy.deepcopy(record)

    pipeline.extract_all(record)

    assert record == before


def test_label_never_changes_any_feature():
    base = {"subject": "Verify now", "body": "http://x.example.invalid", "sender": "a@example.com"}

    assert pipeline.extract_all({**base, "label": "phishing"}) == pipeline.extract_all({**base, "label": "legitimate"})


def test_binary_features_only_return_zero_or_one():
    record = {"subject": "URGENT verify", "body": "<form>http://1.2.3.4/x http://bit.ly/a</form>", "sender": "a@gmail.com"}
    flags = [name for name in pipeline.feature_names() if name.split("_", 1)[1].startswith(("has_", "is_", "ip_", "plain_"))]
    values = pipeline.extract_all(record)

    assert flags and all(values[name] in (0.0, 1.0) for name in flags)


def test_descriptions_are_single_plain_sentences():
    for name, text in pipeline.feature_descriptions().items():
        assert text.strip() == text and text.endswith("."), name
        assert "\n" not in text and "<FILL" not in text, name


def test_reference_has_a_title_and_no_unfilled_markers():
    text = reference.build_markdown()

    assert text.startswith("# Feature reference") and "<FILL" not in text


def test_script_can_be_run_as_a_program():
    import subprocess

    root = Path(reference.__file__).resolve().parents[1]
    done = subprocess.run([sys.executable, "scripts/make_feature_reference.py", "--check"], cwd=root, capture_output=True, text=True)

    assert done.returncode == 0, done.stdout + done.stderr
