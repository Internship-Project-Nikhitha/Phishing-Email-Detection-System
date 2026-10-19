import sys

import joblib
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.predict import main


@pytest.fixture
def trained_model(tmp_path):
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("classifier", LogisticRegression(random_state=42)),
        ]
    )
    model.fit(
        [
            "urgent password account verify",
            "reset your account password now",
            "project meeting agenda update",
            "the report is ready for review",
        ],
        ["phishing", "phishing", "legitimate", "legitimate"],
    )
    artifact = tmp_path / "model.joblib"
    joblib.dump(model, artifact)
    return artifact


def test_predicts_from_text_file_without_printing_email(trained_model, tmp_path, monkeypatch, capsys):
    text = "urgent account password verify"
    email_path = tmp_path / "email.txt"
    email_path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["predict", str(trained_model), "--text-file", str(email_path)],
    )

    main()

    captured = capsys.readouterr()
    assert captured.out.strip() == "phishing"
    assert text not in captured.out
    assert "joblib" in captured.err


def test_predicts_from_stdin(trained_model, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["predict", str(trained_model)])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(sys.stdin, "read", lambda: "project meeting agenda")

    main()

    assert capsys.readouterr().out.strip() == "legitimate"


def test_rejects_empty_text_before_loading_model(trained_model, monkeypatch):
    email_path = trained_model.parent / "empty.txt"
    email_path.write_text(" \n", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["predict", str(trained_model), "--text-file", str(email_path)],
    )

    with pytest.raises(SystemExit, match="Email text is empty"):
        main()


def test_rejects_missing_model_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["predict", str(tmp_path / "missing.joblib")])

    with pytest.raises(SystemExit, match="does not exist"):
        main()