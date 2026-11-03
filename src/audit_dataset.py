"""Print content-safe quality statistics for a configured email dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from src.dataset import DatasetError, load_dataset
from src.quality import audit_dataset


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        help="Path to a dataset JSON config; relative dataset paths resolve beside it",
    )
    args = parser.parse_args(argv)
    config_path = Path(args.config)

    try:
        batch = load_dataset(config_path, base_dir=config_path.resolve().parent)
    except DatasetError as error:
        parser.error(str(error))

    report = audit_dataset(batch.valid)
    report["invalid_record_count"] = len(batch.errors)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
