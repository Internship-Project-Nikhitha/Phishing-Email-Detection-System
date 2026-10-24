"""Report unresolved markers in dataset research and configuration files."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Sequence, TextIO

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = (
    Path("docs/dataset-card.md"),
    Path("docs/dataset-candidates.md"),
    Path("docs/dataset-selection.md"),
    Path("configs/dataset.example.json"),
)
MARKER_RE = re.compile(r"<FILL\b[^>]*>|\b(?:TODO|PENDING|UNVERIFIED)\b", re.IGNORECASE)


def check_pending(paths: Sequence[Path], output: TextIO) -> int:
    """Report marker locations; pending findings are informational, missing files fail."""
    findings = 0
    failures = 0

    for path in paths:
        resolved = path if path.is_absolute() else ROOT / path
        try:
            lines = resolved.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            print(f"ERROR: cannot read {path}: {error}", file=output)
            failures += 1
            continue

        for line_number, line in enumerate(lines, start=1):
            for match in MARKER_RE.finditer(line):
                print(
                    f"{path}:{line_number}: unresolved marker {match.group(0)!r}",
                    file=output,
                )
                findings += 1

    if failures:
        print(f"Could not inspect {failures} required file(s).", file=output)
        return 2
    if findings:
        print(
            f"Reported {findings} pending marker(s); these findings are informational.",
            file=output,
        )
    else:
        print("No pending markers found in the configured dataset files.", file=output)
    return 0


def main() -> int:
    return check_pending(DEFAULT_PATHS, sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
