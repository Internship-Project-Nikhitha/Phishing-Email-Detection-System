"""Small reporting helpers for splits and quality audits (counts and IDs only, no email text)."""

import csv
from pathlib import Path

from src.keys import record_id
from src.quality import QualityAudit
from src.splitting import SPLIT_NAMES, SplitResult

DEFAULT_RATIOS = (0.70, 0.15, 0.15)
DEFAULT_LEVEL = "near"


def summarize_split(result: SplitResult) -> dict[str, dict]:
    """Return ``{split: {"size": n, "labels": {label: count}}}``."""
    summary: dict[str, dict] = {}
    for name in SPLIT_NAMES:
        labels: dict[str, int] = {}
        for record in result.by_name(name):
            labels[record["label"]] = labels.get(record["label"], 0) + 1
        summary[name] = {"size": len(result.by_name(name)), "labels": labels}
    return summary


def write_split_ids(result: SplitResult, path: str | Path) -> int:
    """Write ``split,id,label`` rows (no email text). Return the number of rows."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["split", "id", "label"])
        for name in SPLIT_NAMES:
            for record in result.by_name(name):
                writer.writerow([name, record_id(record), record["label"]])
                rows += 1
    return rows


def format_quality_markdown(audit: QualityAudit, title: str, records: list[dict] | None = None) -> str:
    """Render a ``QualityAudit`` as Markdown tables (counts only).

    Pass ``records`` to add the label distribution table.
    """
    rows = [
        ("Total records", audit.total_records),
        ("Valid records", audit.valid_records),
        ("Invalid records", audit.invalid_records),
        ("Missing-content records", audit.missing_content_records),
        ("Invalid-label records", audit.invalid_label_records),
        ("Exact duplicate groups", audit.exact_duplicate_groups),
        ("Exact duplicate records", audit.exact_duplicate_records),
        ("Near-duplicate groups", audit.near_duplicate_groups),
        ("Near-duplicate records", audit.near_duplicate_records),
        ("Groups with conflicting labels", audit.conflicting_label_groups),
    ]
    lines = [f"## {title}", "", "| Check | Count |", "|---|---|"]
    lines += [f"| {name} | {value} |" for name, value in rows]
    lines.append("")
    if records:
        counts: dict[str, int] = {}
        for record in records:
            counts[record["label"]] = counts.get(record["label"], 0) + 1
        lines += ["### Label distribution", "", "| Label | Records | Share |", "|---|---|---|"]
        for label in sorted(counts):
            lines.append(f"| {label} | {counts[label]} | {counts[label] / len(records):.2%} |")
        lines.append("")
    return "\n".join(lines)


def count_removed(dedup) -> dict[str, int]:
    """Count removed records by reason: duplicates vs. label conflicts vs. malformed."""
    counts = {"duplicates": 0, "conflicts": 0, "malformed": 0}
    for item in dedup.removed:
        if item.reason.startswith("duplicate"):
            counts["duplicates"] += 1
        elif item.reason.startswith("conflicting"):
            counts["conflicts"] += 1
        else:
            counts["malformed"] += 1
    return counts
