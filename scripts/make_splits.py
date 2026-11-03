"""Create the train/validation/test split and save its record IDs (Member 4).

Usage (from the project root):

    python scripts/make_splits.py --config configs/dataset.json --seed 42

Writes ``reports/split_ids.csv`` (IDs and labels only, no email text) and
``reports/split_summary.md``. Stops with an error if any leakage is found.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import data_prep, dataset, split_report, splitting  # noqa: E402


def build_summary(prepared: data_prep.PreparedData, seed: int = 42) -> str:
    """Return a Markdown summary of how the data was split."""
    summary = split_report.summarize_split(prepared.splits)
    train, validation, test = split_report.DEFAULT_RATIOS
    lines = [
        "# Train/validation/test split",
        "",
        f"- Seed: **{seed}**",
        f"- Requested ratios (train/validation/test): {train} / {validation} / {test}",
        f"- Duplicate key level: **{split_report.DEFAULT_LEVEL}**",
        f"- Records after duplicate removal: **{len(prepared.dedup.records)}**",
        f"- Leakage check: **passed** (no content appears in more than one split)",
        f"- Test-set fingerprint: `{splitting.fingerprint_split(prepared.splits, split_report.DEFAULT_LEVEL)}`",
        "",
        "| Split | Records | Phishing | Legitimate |",
        "|---|---|---|---|",
    ]
    for name in splitting.SPLIT_NAMES:
        labels = summary[name]["labels"]
        lines.append(
            f"| {name} | {summary[name]['size']} | {labels.get('phishing', 0)} | {labels.get('legitimate', 0)} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a leakage-safe train/validation/test split.")
    parser.add_argument("--config", default="configs/dataset.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default="reports")
    args = parser.parse_args(argv)

    try:
        prepared = data_prep.prepare_splits(
            args.config, random_state=args.seed, duplicate_level=split_report.DEFAULT_LEVEL
        )
    except (dataset.DatasetError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = split_report.write_split_ids(prepared.splits, out_dir / "split_ids.csv")
    (out_dir / "split_summary.md").write_text(build_summary(prepared, args.seed), encoding="utf-8")
    print(f"Wrote {rows} split IDs and a summary to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
