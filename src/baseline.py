"""Simple baseline classifier: TF-IDF text features + Logistic Regression (Member 5).

A baseline is deliberately simple. Later models must beat it to be worth using.
It reads only the subject and body text. It is trained on the training split
only; validation and test data are never used for fitting.
"""

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

Record = dict[str, str]
POSITIVE_LABEL = "phishing"


def record_text(record: Record) -> str:
    """Join the subject and body of a record into one string for text models."""
    return f"{record.get('subject', '')}\n{record.get('body', '')}"


def build_baseline(max_features: int = 20000, seed: int = 42, c: float = 1.0) -> Pipeline:
    """Create an untrained TF-IDF + Logistic Regression pipeline.

    Args:
        max_features: Maximum vocabulary size.
        seed: Random seed (for reproducibility).
        c: Inverse regularization strength of Logistic Regression.
    """
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True, max_features=max_features),
            ),
            ("classifier", LogisticRegression(C=c, max_iter=2000, class_weight="balanced", random_state=seed)),
        ]
    )


def train_baseline(train_records: list[Record], **kwargs: Any) -> Pipeline:
    """Fit the baseline on training records only.

    Raises:
        ValueError: If there are no records or only one label in the data.
    """
    if not train_records:
        raise ValueError("Cannot train on an empty list of records.")
    labels = [record["label"] for record in train_records]
    if len(set(labels)) < 2:
        raise ValueError("Training data must contain both 'phishing' and 'legitimate' records.")
    model = build_baseline(**kwargs)
    model.fit([record_text(record) for record in train_records], labels)
    return model


def predict_labels(model: Pipeline, records: list[Record]) -> list[str]:
    """Predict ``'phishing'`` or ``'legitimate'`` for each record."""
    return [str(label) for label in model.predict([record_text(record) for record in records])]


def predict_scores(model: Pipeline, records: list[Record]) -> list[float]:
    """Return the model's probability that each record is phishing (0 to 1)."""
    column = list(model.classes_).index(POSITIVE_LABEL)
    probabilities = model.predict_proba([record_text(record) for record in records])
    return [float(row[column]) for row in probabilities]
