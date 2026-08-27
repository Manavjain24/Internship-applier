"""Read job listings from a Google Sheet."""

from pathlib import Path
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from .data_loader import Job


EXPECTED_HEADERS = [
    "ID",
    "Date Added",
    "Company",
    "Job Title",
    "Job Type",
    "Location",
    "Source Platform",
    "Experience",
]

GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def authenticate(credentials_path: str | Path) -> Any:
    """Create an authenticated Google Sheets client using service-account credentials."""
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
    worksheet_name: str,
    credentials_path: str | Path,
) -> list[Job]:
    """Open a worksheet, validate its headers, and return its rows as dictionaries."""
    client = authenticate(credentials_path)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(worksheet_name)
    rows = worksheet.get_all_records()

    actual_headers = worksheet.row_values(1)
    missing_headers = [
        header for header in EXPECTED_HEADERS if header not in actual_headers
    ]
    if missing_headers:
        missing = ", ".join(missing_headers)
        raise ValueError(f"Google Sheet is missing required headers: {missing}")

    return [dict(row) for row in rows]







