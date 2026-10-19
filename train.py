"""Train and evaluate a reproducible TF-IDF/logistic-regression baseline."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.data.dataset_loader import load_dataset
from src.data.validate_dataset import audit_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", help="Local CSV, JSON, or JSONL path")
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--phishing-label", required=True)
    parser.add_argument("--legitimate-label", required=True)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="artifacts/phishing_baseline.joblib")
    parser.add_argument("--group-column", help="Optional source/campaign column for group-held-out split")
    args = parser.parse_args()

    result = load_dataset(
        args.data,
        column_mapping={"text": args.text_column, "label": args.label_column},
        label_mapping={args.phishing_label: "phishing", args.legitimate_label: "legitimate"},
    )
    dataframe = result.dataframe
    if dataframe["label"].nunique() < 2:
        warnings.warn(
            "Dataset contains only one class; a binary model cannot be trained.",
            RuntimeWarning,
        )
        raise SystemExit("Training requires both phishing and legitimate examples; no model was saved.")
    if len(dataframe) < 20:
        warnings.warn("Dataset is very small; metrics and generalization estimates are unstable.", RuntimeWarning)
    if args.group_column:
        if args.group_column not in dataframe.columns:
            raise SystemExit(f"Group column '{args.group_column}' is not present.")
        from sklearn.model_selection import GroupShuffleSplit

        splitter = GroupShuffleSplit(n_splits=1, test_size=args.test_size, random_state=args.seed)
        train_indices, test_indices = next(
            splitter.split(dataframe["text"], dataframe["label"], groups=dataframe[args.group_column])
        )
        train = dataframe.iloc[train_indices]
        test = dataframe.iloc[test_indices]
    else:
        train, test = train_test_split(
            dataframe,
            test_size=args.test_size,
            random_state=args.seed,
            stratify=dataframe["label"] if dataframe["label"].value_counts().min() >= 2 else None,
        )
    if train["label"].nunique() < 2 or test["label"].nunique() < 2:
        raise SystemExit("Both train and test splits must contain both labels; adjust split/data. No model saved.")

    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=100_000)),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=args.seed)),
        ]
    )
    model.fit(train["text"], train["label"])
    predictions = model.predict(test["text"])
    labels = ["legitimate", "phishing"]
    report = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "metrics": {
            "accuracy": accuracy_score(test["label"], predictions),
            "precision_phishing": precision_score(test["label"], predictions, pos_label="phishing", zero_division=0),
            "recall_phishing": recall_score(test["label"], predictions, pos_label="phishing", zero_division=0),
            "f1_phishing": f1_score(test["label"], predictions, pos_label="phishing", zero_division=0),
            "confusion_matrix_labels": labels,
            "confusion_matrix": confusion_matrix(test["label"], predictions, labels=labels).tolist(),
        },
        "quality": audit_dataset(dataframe, train=train, test=test, group_column=args.group_column),
        "loader": result.summary,
        "split": "group-held-out" if args.group_column else "stratified-random" if train["label"].value_counts().min() >= 2 else "random-unstratified",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output)
    print(json.dumps(report, indent=2))
    print(f"Saved baseline pipeline to {output}. Load only artifacts you created or trust.")


if __name__ == "__main__":
    main()