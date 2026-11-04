"""Count rows by source and label in the configured dataset (counts only, no email text).

Usage (from the project root):

    python scripts/dataset_crosstab.py --config configs/dataset.json --source-column source

Why: if every email of one class comes from one source corpus, a model can learn the
source instead of phishing. This table shows whether that is the case.
"""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import dataset  # noqa: E402


def crosstab(config_path: str | Path, source_column: str, base_dir: str | Path | None = None) -> str:
    """Return a Markdown table of row counts by source and raw label."""
    config = dataset.load_config(config_path)
    path = Path(config.path)
    if not path.is_absolute() and base_dir is not None:
        path = Path(base_dir) / path
    if not path.is_file():
        raise dataset.DatasetError(f"Dataset file not found: {path}")
    label_column = config.columns["label"]
    counts: Counter[tuple[str, str]] = Counter()
    csv.field_size_limit(dataset.MAX_FIELD_CHARS)
    try:
        with path.open("r", encoding=config.encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=config.delimiter)
            names = reader.fieldnames or []
            for needed in (source_column, label_column):
                if needed not in names:
                    raise dataset.DatasetError(f"Column {needed!r} not found. Columns: {names}")
            for row in reader:
                counts[((row.get(source_column) or "").strip(), (row.get(label_column) or "").strip())] += 1
    except (OSError, UnicodeError, csv.Error) as error:
        raise dataset.DatasetError(f"Could not read dataset file {path}: {error}") from error
    labels = sorted({label for _, label in counts})
    lines = [f"| {source_column} | " + " | ".join(f"label {label}" for label in labels) + " | total |",
             "|---|" + "---|" * (len(labels) + 1)]
    for source in sorted({s for s, _ in counts}):
        row = [counts[(source, label)] for label in labels]
        lines.append(f"| {source or '(empty)'} | " + " | ".join(str(n) for n in row) + f" | {sum(row)} |")
    total = [sum(counts[(s, label)] for s in {s for s, _ in counts}) for label in labels]
    lines.append("| **all** | " + " | ".join(str(n) for n in total) + f" | {sum(total)} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Count rows by source and label (no email text).")
    parser.add_argument("--config", default="configs/dataset.json")
    parser.add_argument("--source-column", default="source")
    parser.add_argument("--out", default=None, help="write the table to this file instead of printing it")
    args = parser.parse_args(argv)
    try:
        table = crosstab(args.config, args.source_column)
    except dataset.DatasetError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(table, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
