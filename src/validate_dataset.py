"""Quality and privacy-risk checks for normalized email datasets."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

import pandas as pd

from src.data.dataset_loader import DatasetLoadError, load_dataset


EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
HTML_RE = re.compile(r"(?is)<\s*(?:!doctype\b|/?[a-z][a-z0-9:-]*\b[^>]*>)")
IPV4_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d ().-]{7,}\d(?!\w)")


def audit_dataset(
    dataframe: pd.DataFrame,
    *,
    train: pd.DataFrame | None = None,
    test: pd.DataFrame | None = None,
    group_column: str | None = None,
) -> dict[str, Any]:
    """Return content-safe counts and optional split leakage diagnostics."""
    if not {"text", "label"}.issubset(dataframe.columns):
        raise DatasetLoadError("Dataframe must contain canonical 'text' and 'label' columns.")

    texts = dataframe["text"].fillna("").astype(str)
    distribution = dataframe["label"].value_counts().to_dict()
    nonzero = sorted(int(count) for count in distribution.values() if count > 0)
    imbalance = float(nonzero[-1] / nonzero[0]) if len(nonzero) == 2 else None
    report: dict[str, Any] = {
        "rows": int(len(dataframe)),
        "empty_text_rows": int(texts.str.strip().eq("").sum()),
        "exact_duplicate_text_rows": int(texts.duplicated(keep="first").sum()),
        "label_distribution": {str(key): int(value) for key, value in distribution.items()},
        "class_imbalance_ratio": imbalance,
        "email_address_rows": int(texts.str.contains(EMAIL_RE, na=False).sum()),
        "url_rows": int(texts.str.contains(URL_RE, na=False).sum()),
        "ipv4_address_rows": int(texts.str.contains(IPV4_RE, na=False).sum()),
        "phone_like_rows": int(texts.str.contains(PHONE_RE, na=False).sum()),
        "html_rows": int(texts.str.contains(HTML_RE, na=False).sum()),
        "html_is_preserved": True,
        "url_is_preserved": True,
    }
    if train is not None and test is not None:
        if not {"text"}.issubset(train.columns) or not {"text"}.issubset(test.columns):
            raise DatasetLoadError("Train and test frames must contain a 'text' column.")
        train_texts = set(train["text"].dropna().astype(str))
        test_texts = set(test["text"].dropna().astype(str))
        report["train_test_exact_duplicate_texts"] = len(train_texts & test_texts)
        report["group_overlap_count"] = None
        if group_column:
            if group_column not in train.columns or group_column not in test.columns:
                raise DatasetLoadError(f"Group column '{group_column}' must exist in both split frames.")
            train_groups = set(train[group_column].dropna().astype(str))
            test_groups = set(test[group_column].dropna().astype(str))
            report["group_overlap_count"] = len(train_groups & test_groups)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", help="Local CSV, JSON, or JSONL path")
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--phishing-label", required=True)
    parser.add_argument("--legitimate-label", required=True)
    args = parser.parse_args()
    result = load_dataset(
        args.data,
        column_mapping={"text": args.text_column, "label": args.label_column},
        label_mapping={args.phishing_label: "phishing", args.legitimate_label: "legitimate"},
    )
    report = {"loader": result.summary, "quality": audit_dataset(result.dataframe)}
    print(json.dumps(report, indent=2))
    if not result.invalid_rows.empty:
        print("Invalid rows (source row and reason only):")
        print(result.invalid_rows.to_json(orient="records"))


if __name__ == "__main__":
    main()