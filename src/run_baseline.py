"""Command-line entry point for the TF-IDF + Logistic Regression baseline."""
import argparse
import json

from src.baseline_model import run_baseline_experiment


def main():
    parser = argparse.ArgumentParser(
        description="Train and evaluate the phishing-email TF-IDF + Logistic Regression baseline."
    )
    parser.add_argument("--data", required=True, help="Path to the agreed labelled CSV dataset.")
    parser.add_argument("--output-dir", default="outputs/baseline", help="Directory for metric files.")
    parser.add_argument("--text-col", default=None, help="Single text column, if dataset has one.")
    parser.add_argument("--subject-col", default="subject")
    parser.add_argument("--body-col", default="body")
    parser.add_argument("--label-col", default="label")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    metrics = run_baseline_experiment(
        csv_path=args.data,
        output_dir=args.output_dir,
        text_col=args.text_col,
        subject_col=args.subject_col,
        body_col=args.body_col,
        label_col=args.label_col,
        test_size=args.test_size,
        random_state=args.seed,
    )
    print(json.dumps({
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1_score"],
        "false_positive_rate": metrics["false_positive_rate"],
        "confusion_matrix": metrics["confusion_matrix"],
    }, indent=2))


if __name__ == "__main__":
    main()
