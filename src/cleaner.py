"""Normalize job columns and clean text values."""

import re
from typing import Iterable, List

from .data_loader import Job


OUTPUT_COLUMNS = [
    "company",
    "job_title",
    "location",
    "source_platform",
    "salary",
    "date_posted",
    "job_link",
]

COLUMN_ALIASES = {
    "company name": "company",
    "employer": "company",
    "job title": "job_title",
    "title": "job_title",
    "location": "location",
    "source platform": "source_platform",
    "source": "source_platform",
    "salary": "salary",
    "date posted": "date_posted",
    "posted date": "date_posted",
    "loopcv job link": "job_link",
    "job link": "job_link",
    "link": "job_link",
}


def _normalise_column_name(name: str) -> str:
    name = name.strip().lower().replace("_", " ")
    name = re.sub(r"\s+", " ", name)
    return COLUMN_ALIASES.get(name, name.replace(" ", "_"))


def clean_jobs(rows: Iterable[Job]) -> List[Job]:
    """Return rows with consistent column names and trimmed text values."""
    cleaned_rows = []
    for row in rows:
        cleaned = {
            _normalise_column_name(str(key)): str(value or "").strip()
            for key, value in row.items()
            if key is not None
        }
        for column in OUTPUT_COLUMNS:
            cleaned.setdefault(column, "")
        cleaned_rows.append(cleaned)
    return cleaned_rows
