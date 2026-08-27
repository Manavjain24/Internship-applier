"""Classify jobs using only the job title."""

import re
from typing import Dict

from .data_loader import Job


SENIOR_PATTERNS = (
    r"\bsenior\b",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\blead\b",
    r"\bmanager\b",
    r"\bdirector\b",
    r"\barchitect\b",
    r"\bengineer\s+(?:iii|iv|v)\b",
)

HIGH_PATTERNS = (
    r"\bintern(ship)?\b",
    r"\bgraduate\b",
    r"\bjunior\b",
    r"\bentry[- ]level\b",
    r"\btrainee\b",
)

MEDIUM_PATTERNS = (
    r"\bsoftware engineer\b",
    r"\bsoftware developer\b",
    r"\bfull[- ]stack\b",
    r"\bbackend\b",
    r"\bdata engineer(?:ing)?\b",
    r"\bmern\b",
)


def _matches_any(title: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, title, flags=re.IGNORECASE) for pattern in patterns)


def classify_job_title(job_title: str) -> Dict[str, object]:
    """Return priority, score, reason, and default status for a job title."""
    title = job_title.strip()
    if not title:
        return {
            "priority": "Not Applying",
            "relevance_score": 1,
            "classification_reason": "Job title is missing, so relevance cannot be established.",
            "application_status": "Not Applying",
        }
    if _matches_any(title, SENIOR_PATTERNS):
        return {
            "priority": "Not Applying",
            "relevance_score": 1,
            "classification_reason": "Title indicates a senior, leadership, management, or clearly advanced role.",
            "application_status": "Not Applying",
        }
    if _matches_any(title, HIGH_PATTERNS):
        return {
            "priority": "High Priority",
            "relevance_score": 9,
            "classification_reason": "Title indicates an internship, graduate, junior, entry-level, or trainee role.",
            "application_status": "Saved",
        }
    if _matches_any(title, MEDIUM_PATTERNS):
        return {
            "priority": "Medium Priority",
            "relevance_score": 7,
            "classification_reason": "Title matches a software, full-stack, backend, MERN, or data engineering role.",
            "application_status": "Saved",
        }
    return {
        "priority": "Low Priority",
        "relevance_score": 3,
        "classification_reason": "Title does not provide a strong match for the current title-only rules.",
        "application_status": "Saved",
    }


def classify_job(job: Job) -> Job:
    """Add classification fields to a job row."""
    classified = dict(job)
    classified.update(classify_job_title(classified.get("job_title", "")))
    return classified
