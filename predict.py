"""Classify one email locally using a trusted trained model artifact."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="Trusted joblib pipeline created by src.train")
    parser.add_argument("--text-file", help="UTF-8 file containing one email; default reads stdin")
    args = parser.parse_args(argv)

    model_path = Path(args.model).expanduser()
    if not model_path.is_file():
        raise SystemExit(f"Model artifact does not exist or is not a file: {model_path}")

    try:
        if args.text_file:
            email_text = Path(args.text_file).expanduser().read_text(encoding="utf-8")
        elif not sys.stdin.isatty():
            email_text = sys.stdin.read()
        else:
            raise SystemExit("Provide --text-file or pipe email text through stdin.")
    except OSError as exc:
        raise SystemExit(f"Could not read email text file: {exc}") from exc
    except UnicodeError as exc:
        raise SystemExit("Email text file must be valid UTF-8.") from exc

    if not email_text.strip():
        raise SystemExit("Email text is empty; no prediction was made.")

    print(
        "Warning: loading joblib can execute code. Load only a model artifact you created or trust.",
        file=sys.stderr,
    )
    try:
        model = joblib.load(model_path)
    except Exception as exc:
        raise SystemExit("Could not load the trusted joblib model artifact.") from exc

    classes = getattr(model, "classes_", None)
    if classes is None or {str(value) for value in classes} != {"phishing", "legitimate"}:
        raise SystemExit("Model must expose both 'phishing' and 'legitimate' classes.")
    try:
        prediction = str(model.predict([email_text])[0])
    except Exception as exc:
        raise SystemExit("Model could not classify the provided email text.") from exc
    if prediction not in {"phishing", "legitimate"}:
        raise SystemExit("Model returned an unsupported class; expected 'phishing' or 'legitimate'.")

    print(prediction)


if __name__ == "__main__":
    main()