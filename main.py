"""Command-line entry point for processing LoopCV job exports."""

import argparse
import csv
import os
import sys
from json import dumps
from pathlib import Path
from typing import Iterable, List

from src.classifier import classify_job
from src.cleaner import OUTPUT_COLUMNS, clean_jobs
from src.data_loader import Job, load_jobs
from src.deduplicator import remove_duplicates
from src.google_sheets import get_jobs_from_sheet_url
from src.google_sheets import open_spreadsheet, sync_application_queue
from src.application_assistant import prepare_application
from src.application_queue import QUEUE_COLUMNS, job_identity
from src.job_analysis import analyze_job
from src.tracker import build_followups, dashboard_metrics

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


def save_queue_rows(rows: Iterable[Job], output_path: str | Path) -> None:
    """Write queue rows to a local CSV for non-Google workflows."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=QUEUE_COLUMNS)
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in QUEUE_COLUMNS} for row in rows)


def load_input(source: str, credentials_path: str | None, worksheet_name: str | None) -> List[Job]:
    """Load jobs from a local CSV or an authenticated Google Sheet URL."""
    if source.startswith("https://docs.google.com/spreadsheets/"):
        if not credentials_path:
            raise ValueError(
                "Google Sheet input requires --google-credentials pointing to a service-account JSON file"
            )
        return get_jobs_from_sheet_url(source, credentials_path, worksheet_name)
    return load_jobs(source)


DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1AKxetFFGWOwYhPdbg672x-sh7P0qU-uyiF2V4MFX3t4/edit?gid=0#gid=0"


def sync_command(arguments: list[str]) -> None:
    """Preview or explicitly apply a safe Application Queue synchronization."""
    parser = argparse.ArgumentParser(description="Synchronize the Google Sheet Application Queue.")
    parser.add_argument("--sheet-url", default=os.getenv("GOOGLE_SHEET_URL", DEFAULT_SHEET_URL))
    parser.add_argument("--google-credentials", default=os.getenv("GOOGLE_CREDENTIALS"))
    parser.add_argument("--worksheet", default=os.getenv("GOOGLE_JOBS_WORKSHEET", "Jobs"))
    parser.add_argument("--queue-worksheet", default=os.getenv("GOOGLE_QUEUE_WORKSHEET", "Application Queue"))
    parser.add_argument("--input", help="Local CSV source; omits Google access when supplied")
    parser.add_argument("--local-output", default="data/output/application_queue.csv", help="Local queue CSV path")
    parser.add_argument("--apply", action="store_true", help="Apply queue changes after reviewing a previous dry run")
    args = parser.parse_args(arguments)
    if not args.input and not args.google_credentials:
        parser.error("Set GOOGLE_CREDENTIALS or provide --google-credentials.")

    try:
        spreadsheet = None
        if args.input:
            source_rows = load_jobs(args.input)
            print(f"CSV source: {args.input}")
        else:
            from src.google_sheets import extract_sheet_id
            spreadsheet = open_spreadsheet(extract_sheet_id(args.sheet_url), args.google_credentials)
            print("Worksheets:", ", ".join(worksheet.title for worksheet in spreadsheet.worksheets()))
            source_rows = spreadsheet.worksheet(args.worksheet).get_all_records()
        if not source_rows:
            parser.error(f"Worksheet '{args.worksheet}' is empty.")
        print("Jobs columns:", ", ".join(str(column) for column in source_rows[0]))
        print(f"Jobs detected: {len(source_rows)}")
        processed_jobs = process_jobs([dict(row) for row in source_rows])
        if args.input:
            existing_rows = load_jobs(args.local_output) if Path(args.local_output).exists() else []
            from src.application_queue import sync_queue_rows
            plan = sync_queue_rows(processed_jobs, existing_rows)
            if args.apply:
                new_rows, updated_rows, unchanged_rows = plan
                rows_by_identity = {job_identity(row): row for row in existing_rows}
                rows_by_identity.update({job_identity(row): row for row in unchanged_rows})
                rows_by_identity.update({job_identity(row): row for row in updated_rows})
                rows_by_identity.update({job_identity(row): row for row in new_rows})
                save_queue_rows(rows_by_identity.values(), args.local_output)
        else:
            plan = sync_application_queue(spreadsheet, processed_jobs, worksheet_name=args.queue_worksheet, apply_changes=args.apply)
        new_rows, updated_rows, unchanged_rows = plan
        print(f"Relevant jobs: {len(new_rows) + len(updated_rows) + len(unchanged_rows)}")
        print(f"New queue rows: {len(new_rows)}")
        print(f"Updated queue rows: {len(updated_rows)}")
        print(f"Preserved queue rows: {len(unchanged_rows)}")
        print("Preview:", dumps({"new": new_rows, "updated": updated_rows}, indent=2, default=str))
        print("Changes applied." if args.apply else "Dry run only; no Google Sheet changes were made.")
    except (FileNotFoundError, PermissionError, ValueError, RuntimeError) as error:
        parser.error(str(error))


def queue_rows_command(arguments: list[str], action: str) -> None:
    """Run a read-only report against the current Application Queue."""
    parser = argparse.ArgumentParser(description=f"Read-only Application Queue {action} report.")
    parser.add_argument("--sheet-url", default=os.getenv("GOOGLE_SHEET_URL", DEFAULT_SHEET_URL))
    parser.add_argument("--google-credentials", default=os.getenv("GOOGLE_CREDENTIALS"))
    parser.add_argument("--queue-worksheet", default=os.getenv("GOOGLE_QUEUE_WORKSHEET", "Application Queue"))
    parser.add_argument("--queue-csv", default="data/output/application_queue.csv", help="Local queue CSV path")
    parser.add_argument("--id", help="Stable job identity, required by the apply command")
    args = parser.parse_args(arguments)
    if not args.google_credentials and not Path(args.queue_csv).exists():
        parser.error("Set GOOGLE_CREDENTIALS or provide --google-credentials.")
    try:
        if Path(args.queue_csv).exists() and not args.google_credentials:
            rows = load_jobs(args.queue_csv)
        else:
            from src.google_sheets import extract_sheet_id, get_worksheet_rows
            spreadsheet = open_spreadsheet(extract_sheet_id(args.sheet_url), args.google_credentials)
            rows = get_worksheet_rows(spreadsheet, args.queue_worksheet)
        if action == "analyze":
            print(dumps([analyze_job(row) | {"company": row.get("company", ""), "job_title": row.get("job_title", "")} for row in rows], indent=2))
        elif action == "followups":
            print(dumps(build_followups(rows), indent=2))
        elif action == "dashboard":
            print(dumps(dashboard_metrics(rows), indent=2))
        elif action == "apply":
            if not args.id:
                parser.error("--id is required for apply preparation.")
            matching = next((row for row in rows if job_identity(row) == args.id), None)
            if matching is None:
                parser.error(f"No queue job found for id '{args.id}'.")
            print(dumps(prepare_application(matching), indent=2))
            print("Stopped before submission; human confirmation is required.")
    except (FileNotFoundError, PermissionError, ValueError, RuntimeError) as error:
        parser.error(str(error))


def main() -> None:
    commands = {"sync": sync_command, "analyze": lambda args: queue_rows_command(args, "analyze"), "followups": lambda args: queue_rows_command(args, "followups"), "dashboard": lambda args: queue_rows_command(args, "dashboard"), "apply": lambda args: queue_rows_command(args, "apply")}
    if len(sys.argv) > 1 and sys.argv[1] in commands:
        commands[sys.argv[1]](sys.argv[2:])
        return
    parser = argparse.ArgumentParser(description="Process LoopCV job listings from CSV or Google Sheets.")
    parser.add_argument(
        "input",
        nargs="?",
        default="data/input/sample_jobs.csv",
        help="Input CSV path or Google Sheet URL (default: data/input/sample_jobs.csv)",
    )
    parser.add_argument(
        "--google-credentials",
        help="Path to the Google service-account JSON file (required for Google Sheet input)",
    )
    parser.add_argument(
        "--worksheet",
        help="Worksheet tab name (default: first tab)",
    )
    parser.add_argument(
        "--output",
        default="data/output/processed_jobs.csv",
        help="Output CSV path (default: data/output/processed_jobs.csv)",
    )
    args = parser.parse_args()

    try:
        processed_jobs = process_jobs(load_input(args.input, args.google_credentials, args.worksheet))
        save_jobs(processed_jobs, args.output)
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    print(f"Processed {len(processed_jobs)} unique jobs.")
    print(f"Saved results to {args.output}")


if __name__ == "__main__":
    main()
