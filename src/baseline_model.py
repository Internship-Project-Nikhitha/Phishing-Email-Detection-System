"""TF-IDF + Logistic Regression baseline for phishing email detection.

Label convention: 1 = phishing, 0 = legitimate.
The model uses subject and body text only; sender is deliberately excluded
to reduce the chance of learning sender-specific shortcuts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


PHISHING_LABELS = {"phishing", "phish", "phishing email", "malicious", "1"}
LEGITIMATE_LABELS = {
    "legitimate", "legit", "ham", "safe", "safe email", "benign", "0"
}


def normalize_binary_label(value) -> int:
    """Convert project-supported labels to 1 (phishing) or 0 (legitimate)."""
    if isinstance(value, bool) or value is None:
        raise ValueError(f"Unsupported label: {value!r}")
    normalized = str(value).strip().lower().replace("_", " ").replace("-", " ")
    if normalized in PHISHING_LABELS:
        return 1
    if normalized in LEGITIMATE_LABELS:
        return 0
    raise ValueError(
        f"Unknown label {value!r}. Map it explicitly to phishing or legitimate "
        "before running the baseline."
    )


def combine_email_text(
    df: pd.DataFrame,
    subject_col: str = "subject",
    body_col: str = "body",
) -> pd.Series:
    """Combine subject/body into one text field without using sender metadata."""
    missing = [c for c in (subject_col, body_col) if c not in df.columns]
    if missing:
        raise ValueError(f"Missing text column(s): {missing}. Available: {list(df.columns)}")
    subject = df[subject_col].fillna("").astype(str).str.strip()
    body = df[body_col].fillna("").astype(str).str.strip()
    text = (subject + " " + body).str.strip()
    if (text == "").any():
        raise ValueError(
            f"Found {(text == '').sum()} row(s) with empty subject and body. "
            "Clean/drop these rows using the team's agreed preprocessing first."
        )
    return text


def build_baseline_pipeline() -> Pipeline:
    """Create the baseline pipeline; TF-IDF is fitted only on training text."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    max_features=50_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1_000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def calculate_metrics(y_true: Iterable[int], y_pred: Iterable[int]) -> dict:
    """Calculate metrics for phishing class (positive label = 1)."""
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = (int(v) for v in cm.ravel())
    fpr = float(fp / (fp + tn)) if (fp + tn) else None
    return {
        "positive_class": "phishing (label=1)",
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "false_positive_rate": fpr,
        "confusion_matrix": {
            "labels_order": ["legitimate (0)", "phishing (1)"],
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "matrix": cm.tolist(),
        },
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["legitimate", "phishing"],
            output_dict=True,
            zero_division=0,
        ),
    }


def run_baseline_experiment(
    csv_path: str | Path,
    output_dir: str | Path = "outputs/baseline",
    text_col: str | None = None,
    subject_col: str = "subject",
    body_col: str = "body",
    label_col: str = "label",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """Load CSV, make a stratified holdout split, train and save genuine metrics.

    If text_col is given, that column is used directly. Otherwise subject and
    body are combined. The input dataset must already follow the team's agreed
    cleaning/preprocessing rules.
    """
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if label_col not in df.columns:
        raise ValueError(f"Label column {label_col!r} not found. Columns: {list(df.columns)}")

    if text_col:
        if text_col not in df.columns:
            raise ValueError(f"Text column {text_col!r} not found. Columns: {list(df.columns)}")
        X = df[text_col].fillna("").astype(str).str.strip()
        if (X == "").any():
            raise ValueError(f"Found {(X == '').sum()} empty text row(s); clean/drop them first.")
    else:
        X = combine_email_text(df, subject_col=subject_col, body_col=body_col)

    y = df[label_col].map(normalize_binary_label)
    if y.nunique() != 2:
        raise ValueError("Dataset must contain both classes: legitimate and phishing.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = build_baseline_pipeline()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    metrics = calculate_metrics(y_test, y_pred)
    metrics.update({
        "dataset_path": str(csv_path),
        "dataset_rows_used": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "test_size": float(test_size),
        "random_state": int(random_state),
        "text_columns": [text_col] if text_col else [subject_col, body_col],
        "label_column": label_col,
        "model": "TF-IDF (unigrams+bigrams) + Logistic Regression",
        "notes": [
            "Metrics are calculated from this run's held-out test split.",
            "TF-IDF is fitted inside the pipeline on training text only.",
            "Sender metadata is not used when subject/body mode is selected.",
            "These results do not establish generalization to other datasets."
        ],
    })

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    cm = metrics["confusion_matrix"]
    pd.DataFrame(
        [[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]],
        index=["actual_legitimate", "actual_phishing"],
        columns=["predicted_legitimate", "predicted_phishing"],
    ).to_csv(out / "confusion_matrix.csv")
    pd.DataFrame(metrics["classification_report"]).transpose().to_csv(
        out / "classification_report.csv"
    )
    pd.DataFrame([{
        key: metrics[key]
        for key in ("accuracy", "precision", "recall", "f1_score", "false_positive_rate")
    }]).to_csv(out / "summary_metrics.csv", index=False)

    return metrics
