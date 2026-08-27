"""Remove duplicate job listings."""

from typing import Iterable, List, Set, Tuple

from .data_loader import Job


def _duplicate_key(job: Job) -> Tuple[str, str, str]:
    """Build a case-insensitive key from the requested identifying fields."""
    return tuple(job.get(field, "").casefold() for field in ("company", "job_title", "location"))


def remove_duplicates(rows: Iterable[Job]) -> List[Job]:
    """Keep the first listing for each company, title, and location combination."""
    seen: Set[Tuple[str, str, str]] = set()
    unique_rows = []
    for row in rows:
        key = _duplicate_key(row)
        if key in seen:
            continue
        seen.add(key)
        unique_row = dict(row)
        unique_row["is_duplicate"] = "False"
        unique_rows.append(unique_row)
    return unique_rows
