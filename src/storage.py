"""SQLite storage for analysis history (Member 2).

Privacy: by default only a SHA-256 hash of the email and the result are stored,
not the email text. A short subject preview is stored only if the caller
passes one. All SQL uses placeholders (``?``), never string formatting.
"""

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    source_name TEXT NOT NULL DEFAULT '',
    content_sha256 TEXT NOT NULL DEFAULT '',
    subject_preview TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL,
    score REAL NOT NULL,
    risk_level TEXT NOT NULL,
    model_version TEXT NOT NULL,
    indicators_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]'
)
"""
PREVIEW_LENGTH = 80
REQUIRED_RESULT_KEYS = ("label", "score", "risk_level", "model_version")


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open (and create if needed) the history database.

    Args:
        path: A file path, or ``':memory:'`` for a temporary database.

    Returns:
        A connection whose rows behave like dicts. Open one connection per
        request or thread; SQLite connections should not be shared across threads.
    """
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the history table if it does not exist."""
    conn.execute(SCHEMA)
    conn.commit()


def _preview(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()[:PREVIEW_LENGTH]


def save_analysis(
    conn: sqlite3.Connection,
    result: dict[str, Any],
    source_name: str = "",
    content_sha256: str = "",
    subject_preview: str = "",
    now: datetime | None = None,
) -> int:
    """Store one analysis result and return its new ID.

    Args:
        conn: Connection from ``connect``.
        result: Analysis dict with ``label``, ``score``, ``risk_level``,
            ``model_version`` and optionally ``indicators`` and ``warnings``.
        source_name: Name of the uploaded file (display only).
        content_sha256: Hash identifying the email content.
        subject_preview: Optional short subject text (cut to 80 characters).
        now: Timestamp to record (defaults to the current UTC time).

    Raises:
        ValueError: If a required key is missing from ``result``.
    """
    missing = [key for key in REQUIRED_RESULT_KEYS if key not in result]
    if missing:
        raise ValueError(f"Analysis result is missing keys: {missing}")
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cursor = conn.execute(
        "INSERT INTO analysis_history (created_at, source_name, content_sha256, subject_preview, label, score,"
        " risk_level, model_version, indicators_json, warnings_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            moment.isoformat(timespec="seconds"),
            str(source_name)[:200],
            content_sha256,
            _preview(subject_preview),
            result["label"],
            float(result["score"]),
            result["risk_level"],
            result["model_version"],
            json.dumps(result.get("indicators", [])),
            json.dumps(result.get("warnings", [])),
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


# @@PART 2
def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["indicators"] = json.loads(data.pop("indicators_json"))
    data["warnings"] = json.loads(data.pop("warnings_json"))
    return data


def list_history(conn: sqlite3.Connection, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Return stored analyses, newest first.

    Raises:
        ValueError: If ``limit`` is not 1..1000 or ``offset`` is negative.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000.")
    if offset < 0:
        raise ValueError("offset must not be negative.")
    rows = conn.execute(
        "SELECT * FROM analysis_history ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_analysis(conn: sqlite3.Connection, analysis_id: int) -> dict[str, Any] | None:
    """Return one stored analysis by ID, or ``None`` if it does not exist."""
    row = conn.execute("SELECT * FROM analysis_history WHERE id = ?", (analysis_id,)).fetchone()
    return None if row is None else _row_to_dict(row)


def clear_history(conn: sqlite3.Connection) -> int:
    """Delete all stored analyses and return how many were removed."""
    cursor = conn.execute("DELETE FROM analysis_history")
    conn.commit()
    return cursor.rowcount
