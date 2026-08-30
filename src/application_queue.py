"""Build and synchronize application-queue rows without side effects."""

from datetime import date
from typing import Iterable

from .data_loader import Job


QUEUE_COLUMNS = [
    "id",
    "company",
    "job_title",
    "location",
    "source_platform",
    "salary",
    "date_posted",
    "job_link",
    "priority",
    "relevance_score",
    "classification_reason",
    "application_status",
    "application_method",
    "application_url",
    "next_action",
    "follow_up_date",
    "date_applied",
    "notes",
    "last_checked",
]

MANUAL_FIELDS = (
    "application_status",
    "application_method",
    "application_url",
    "next_action",
    "follow_up_date",
    "date_applied",
    "notes",
)

DEFAULT_MANUAL_VALUES = {
    "application_status": "Saved",
    "application_method": "Unknown",
    "application_url": "",
    "next_action": "Review job",
    "follow_up_date": "",
    "date_applied": "",
    "notes": "",
}


def job_identity(job: Job) -> str:
    """Return the stable, case-insensitive identity for a job."""
    return "|".join(
        str(job.get(field, "")).strip().casefold()
        for field in ("company", "job_title", "location")
    )


def filter_queue_jobs(rows: Iterable[Job]) -> list[Job]:
    """Keep relevant jobs that are not explicitly excluded from pursuing."""
    return [
        row
        for row in rows
        if row.get("priority") != "Not Applying"
        and row.get("application_status") not in {"Rejected", "Not Applying"}
    ]


def _source_fields(job: Job) -> dict[str, str]:
    return {column: str(job.get(column, "")) for column in QUEUE_COLUMNS[:11]}


def build_queue_row(job: Job, checked_on: str | None = None) -> Job:
    """Create a queue row with safe defaults for manually maintained fields."""
    row = _source_fields(job)
    row["id"] = str(job.get("id") or job_identity(job))
    row.update(DEFAULT_MANUAL_VALUES)
    row["last_checked"] = checked_on or date.today().isoformat()
    return row


def sync_queue_rows(
    processed_jobs: Iterable[Job],
    existing_rows: Iterable[Job],
    checked_on: str | None = None,
) -> tuple[list[Job], list[Job], list[Job]]:
    """Plan queue changes as ``(new, updated, unchanged)`` without writing data."""
    existing_by_identity = {job_identity(row): row for row in existing_rows}
    new_rows: list[Job] = []
    updated_rows: list[Job] = []
    unchanged_rows: list[Job] = []

    for processed_job in filter_queue_jobs(processed_jobs):
        identity = job_identity(processed_job)
        existing = existing_by_identity.get(identity)
        if existing is None:
            new_rows.append(build_queue_row(processed_job, checked_on))
            continue

        updated = dict(existing)
        updated.update(_source_fields(processed_job))
        updated["id"] = existing.get("id") or processed_job.get("id") or identity
        updated["last_checked"] = checked_on or date.today().isoformat()
        for field in MANUAL_FIELDS:
            updated[field] = existing.get(field, "")
        if updated["application_status"] == "Applied" and not updated["date_applied"]:
            updated["date_applied"] = checked_on or date.today().isoformat()
        if updated == existing:
            unchanged_rows.append(updated)
        else:
            updated_rows.append(updated)

    return new_rows, updated_rows, unchanged_rows