"""Load job listings from CSV files."""

import csv
from pathlib import Path
from typing import Dict, List


Job = Dict[str, str]


def load_jobs(file_path: str | Path) -> List[Job]:
    """Read a CSV file and return each row as a dictionary."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input CSV file was not found: {path}")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            return [dict(row) for row in csv.DictReader(csv_file)]
    except csv.Error as error:
        raise ValueError(f"Could not read CSV file: {path}") from error
