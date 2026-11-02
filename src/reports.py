"""Export analysis results as JSON, Markdown or CSV (Member 2).

Exports contain only the analysis result (scores, indicators, hashes), never the
email text. CSV cells that could be run as spreadsheet formulas are neutralized.
"""

import csv
import io
import json
from typing import Any

CSV_COLUMNS = ("id", "created_at", "source_name", "label", "score", "risk_level", "model_version", "content_sha256")
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
DISCLAIMER = (
    "This is an automated assessment and may be wrong. A person should review it before acting. "
    "Links in the email were not opened and attachments were not executed."
)


def sanitize_csv_cell(value: Any) -> str:
    """Return ``value`` as text, with a leading ``'`` if a spreadsheet could treat it as a formula."""
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


def analysis_to_json(analysis: dict[str, Any]) -> str:
    """Return the analysis as indented JSON text."""
    return json.dumps(analysis, indent=2, sort_keys=True, default=str)


def _escape_cell(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def analysis_to_markdown(analysis: dict[str, Any]) -> str:
    """Return a short Markdown report for one analysis (as stored by ``storage``)."""
    lines = [
        f"# Phishing analysis report #{analysis.get('id', '-')}",
        "",
        f"- **Result:** {_escape_cell(analysis['label'])}",
        f"- **Risk level:** {_escape_cell(analysis['risk_level'])}",
        f"- **Score:** {analysis['score']}",
        f"- **Model version:** {_escape_cell(analysis['model_version'])}",
        f"- **Analyzed at:** {_escape_cell(analysis.get('created_at', '-'))}",
        f"- **Source:** {_escape_cell(analysis.get('source_name') or '-')}",
        f"- **Content hash (SHA-256):** `{_escape_cell(analysis.get('content_sha256') or '-')}`",
        "",
        "## Warning indicators",
        "",
    ]
    indicators = analysis.get("indicators") or []
    if indicators:
        lines += ["| Indicator | Why it matters | Contribution |", "|---|---|---|"]
        for item in indicators:
            lines.append(
                f"| {_escape_cell(item['feature'])} | {_escape_cell(item['description'])} | {item['contribution']} |"
            )
    else:
        lines.append("No indicators pointed toward phishing.")
    warnings = analysis.get("warnings") or []
    if warnings:
        lines += ["", "## Warnings", ""] + [f"- {_escape_cell(text)}" for text in warnings]
    lines += ["", "---", f"_{DISCLAIMER}_", ""]
    return "\n".join(lines)


def history_to_csv(rows: list[dict[str, Any]]) -> str:
    """Return history rows as CSV text with safe cells (no email content)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        writer.writerow([sanitize_csv_cell(row.get(column)) for column in CSV_COLUMNS])
    return buffer.getvalue()
