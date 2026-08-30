"""Follow-up rows and dashboard metrics derived from queue rows."""

from datetime import date
from typing import Iterable

from .data_loader import Job


def build_followups(rows: Iterable[Job], today: date | None = None) -> list[Job]:
    """Return applications with a follow-up date or active interview/assessment status."""
    current_day = today or date.today()
    result = []
    for row in rows:
        follow_up = str(row.get("follow_up_date", "")).strip()
        status = str(row.get("application_status", "")).strip()
        if not follow_up and status not in {"Assessment", "Interview"}:
            continue
        days_remaining = "Unknown / Not provided"
        if follow_up:
            try:
                days_remaining = str((date.fromisoformat(follow_up) - current_day).days)
            except ValueError:
                days_remaining = "Invalid date"
        result.append({
            "company": row.get("company", ""),
            "job_title": row.get("job_title", ""),
            "application_status": status,
            "date_applied": row.get("date_applied", ""),
            "follow_up_date": follow_up,
            "next_action": row.get("next_action", ""),
            "days_remaining": days_remaining,
            "notes": row.get("notes", ""),
        })
    return result


def dashboard_metrics(rows: Iterable[Job], total_jobs: int | None = None) -> dict[str, int]:
    """Count queue statuses and priorities for a compact dashboard."""
    queue = list(rows)
    metrics = {"total_jobs": total_jobs if total_jobs is not None else len(queue), "relevant_jobs": len(queue)}
    for key in ("high_priority_jobs", "saved", "ready_to_apply", "applied", "assessments", "interviews", "offers", "rejected"):
        metrics[key] = 0
    for row in queue:
        if row.get("priority") == "High Priority":
            metrics["high_priority_jobs"] += 1
        status_key = {
            "Saved": "saved", "Ready to Apply": "ready_to_apply", "Applied": "applied",
            "Assessment": "assessments", "Interview": "interviews", "Offer": "offers", "Rejected": "rejected",
        }.get(str(row.get("application_status", "")))
        if status_key:
            metrics[status_key] += 1
    return metrics