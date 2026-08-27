"""Command-line entry point for processing LoopCV job exports."""

import argparse
import csv
from pathlib import Path
from typing import Iterable, List

from src.classifier import classify_job
from src.cleaner import OUTPUT_COLUMNS, clean_jobs
from src.data_loader import Job, load_jobs
from src.deduplicator import remove_duplicates

OUTPUT_COLUMNS_WITH_RESULTS = OUTPUT_COLUMNS + [
    "is_duplicate",
    "priority",
    "relevance_score",
    "classification_reason",
    "application_status",
]


def process_jobs(rows: Iterable[Job]) -> List[Job]:
    """Clean, deduplicate, and classify job listings."""
    unique_jobs = remove_duplicates(clean_jobs(rows))
    return [classify_job(job) for job in unique_jobs]


def save_jobs(rows: Iterable[Job], output_path: str | Path) -> None:
    """Write processed jobs to a CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_COLUMNS_WITH_RESULTS)
        writer.writeheader()
        writer.writerows(
            {column: row.get(column, "") for column in OUTPUT_COLUMNS_WITH_RESULTS}
            for row in rows
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Process LoopCV job listings from CSV.")
    parser.add_argument(
        "input",
        nargs="?",
        default="data/input/sample_jobs.csv",
        help="Input CSV path (default: data/input/sample_jobs.csv)",
    )
    parser.add_argument(
        "--output",
        default="data/output/processed_jobs.csv",
        help="Output CSV path (default: data/output/processed_jobs.csv)",
    )
    args = parser.parse_args()

    try:
        processed_jobs = process_jobs(load_jobs(args.input))
        save_jobs(processed_jobs, args.output)
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    print(f"Processed {len(processed_jobs)} unique jobs.")
    print(f"Saved results to {args.output}")


if __name__ == "__main__":
    main()
