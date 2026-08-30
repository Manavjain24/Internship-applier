"""Read job listings from a Google Sheet."""

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .data_loader import Job
from .application_queue import QUEUE_COLUMNS, sync_queue_rows


GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def extract_sheet_id(sheet_url: str) -> str:
    """Extract a spreadsheet ID from a Google Sheets URL."""
    parsed_url = urlparse(sheet_url)
    path_parts = parsed_url.path.strip("/").split("/")
    if parsed_url.netloc != "docs.google.com" or len(path_parts) < 3:
        raise ValueError("Google Sheet URL must look like https://docs.google.com/spreadsheets/d/<id>/edit")
    if path_parts[0] != "spreadsheets" or path_parts[1] != "d" or not path_parts[2]:
        raise ValueError("Google Sheet URL must contain a spreadsheet ID")
    return path_parts[2]


def authenticate(credentials_path: str | Path) -> Any:
    """Create an authenticated Google Sheets client using service-account credentials."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as error:
        raise RuntimeError(
            "Google Sheet support requires dependencies from requirements.txt; run "
            "python -m pip install -r requirements.txt"
        ) from error

    path = Path(credentials_path)
    if not path.exists():
        raise FileNotFoundError(f"Google credentials file was not found: {path}")

    credentials = Credentials.from_service_account_file(
        path,
        scopes=GOOGLE_SHEETS_SCOPES,
    )
    return gspread.authorize(credentials)


def get_jobs_from_sheet(
    sheet_id: str,
    worksheet_name: str | None,
    credentials_path: str | Path,
) -> list[Job]:
    """Open a worksheet and return its rows as dictionaries."""
    client = authenticate(credentials_path)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.sheet1
    return [dict(row) for row in worksheet.get_all_records()]


def get_jobs_from_sheet_url(
    sheet_url: str,
    credentials_path: str | Path,
    worksheet_name: str | None = None,
) -> list[Job]:
    """Open a Google Sheet URL and return rows from the selected worksheet."""
    return get_jobs_from_sheet(
        extract_sheet_id(sheet_url),
        worksheet_name,
        credentials_path,
    )


def open_spreadsheet(sheet_id: str, credentials_path: str | Path) -> Any:
    """Authenticate and open a spreadsheet, translating common API failures."""
    try:
        return authenticate(credentials_path).open_by_key(sheet_id)
    except Exception as error:
        error_text = str(error).lower()
        if "permission" in error_text or "403" in error_text:
            raise PermissionError("The service account cannot access this spreadsheet.") from error
        if "not found" in error_text or "404" in error_text:
            raise FileNotFoundError("The spreadsheet was not found or is not shared with the service account.") from error
        raise RuntimeError(f"Could not open Google Sheet: {error}") from error


def get_worksheet_rows(spreadsheet: Any, worksheet_name: str) -> list[Job]:
    """Read records from a named worksheet without modifying it."""
    try:
        return [dict(row) for row in spreadsheet.worksheet(worksheet_name).get_all_records()]
    except Exception as error:
        raise ValueError(f"Could not read worksheet '{worksheet_name}': {error}") from error


def sync_application_queue(
    spreadsheet: Any,
    processed_jobs: list[Job],
    worksheet_name: str = "Application Queue",
    apply_changes: bool = False,
) -> tuple[list[Job], list[Job], list[Job]]:
    """Preview or apply queue changes; never writes to the source worksheet."""
    try:
        queue = spreadsheet.worksheet(worksheet_name)
        existing_rows = [dict(row) for row in queue.get_all_records()]
    except Exception as error:
        if error.__class__.__name__ != "WorksheetNotFound":
            raise RuntimeError(f"Could not read worksheet '{worksheet_name}': {error}") from error
        if not apply_changes:
            return sync_queue_rows(processed_jobs, [])
        try:
            queue = spreadsheet.add_worksheet(worksheet_name, rows=100, cols=len(QUEUE_COLUMNS))
            queue.append_row(QUEUE_COLUMNS, value_input_option="RAW")
            existing_rows = []
        except Exception as create_error:
            raise RuntimeError(
                f"Worksheet '{worksheet_name}' does not exist. Creation failed: {create_error}"
            ) from error

    plan = sync_queue_rows(processed_jobs, existing_rows)
    if not apply_changes:
        return plan

    new_rows, updated_rows, _ = plan
    if new_rows:
        queue.append_rows(
            [[row.get(column, "") for column in QUEUE_COLUMNS] for row in new_rows],
            value_input_option="RAW",
        )

    if updated_rows:
        all_values = queue.get_all_values()
        row_numbers = {
            "|".join(str(value).strip().casefold() for value in (row[1], row[2], row[3])): index
            for index, row in enumerate(all_values[1:], start=2)
            if len(row) >= 4
        }
        updates = []
        for row in updated_rows:
            row_number = row_numbers.get("|".join(
                str(row.get(field, "")).strip().casefold()
                for field in ("company", "job_title", "location")
            ))
            if row_number:
                updates.append({
                    "range": f"A{row_number}:S{row_number}",
                    "values": [[row.get(column, "") for column in QUEUE_COLUMNS]],
                })
        if updates:
            queue.batch_update(updates, raw=True)

    return plan







