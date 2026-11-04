import pandas as pd
import pytest

from src.baseline_model import (
    calculate_metrics,
    combine_email_text,
    normalize_binary_label,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("phishing", 1),
        ("Phish", 1),
        ("malicious", 1),
        (1, 1),
        ("legitimate", 0),
        ("Safe_Email", 0),
        ("ham", 0),
        (0, 0),
    ],
)
def test_normalize_binary_label(value, expected):
    assert normalize_binary_label(value) == expected


@pytest.mark.parametrize("value", ["spam", "suspicious", 2, True, None])
def test_unknown_labels_are_rejected(value):
    with pytest.raises(ValueError):
        normalize_binary_label(value)


def test_combine_subject_and_body():
    df = pd.DataFrame({
        "subject": ["  Account alert  ", None],
        "body": ["Verify now", "Hello"],
    })
    assert combine_email_text(df).tolist() == ["Account alert Verify now", "Hello"]


def test_combine_rejects_empty_email():
    df = pd.DataFrame({"subject": [" "], "body": [None]})
    with pytest.raises(ValueError, match="empty subject and body"):
        combine_email_text(df)


def test_metrics_confusion_matrix_and_false_positive_rate():
    # TN=2, FP=1, FN=1, TP=2 => FPR = 1 / (1+2)
    result = calculate_metrics(
        y_true=[0, 0, 0, 1, 1, 1],
        y_pred=[0, 0, 1, 0, 1, 1],
    )
    assert result["confusion_matrix"]["tn"] == 2
    assert result["confusion_matrix"]["fp"] == 1
    assert result["confusion_matrix"]["fn"] == 1
    assert result["confusion_matrix"]["tp"] == 2
    assert result["false_positive_rate"] == pytest.approx(1 / 3)
