"""Human-controlled application preparation helpers."""

from pathlib import Path

from .data_loader import Job
from .route_discovery import discover_route


def prepare_application(job: Job, resume_path: str | Path | None = None) -> dict[str, object]:
    """Prepare a review summary and explicitly stop before application submission."""
    route = discover_route(job)
    resume = str(resume_path) if resume_path and Path(resume_path).exists() else "Missing resume"
    return {
        "company": job.get("company", ""),
        "job_title": job.get("job_title", ""),
        "application_url": route["application_url"],
        "application_method": route["application_method"],
        "resume_selected": resume,
        "fields_filled": [],
        "questions_requiring_answers": ["Unknown / Not provided"],
        "potential_concerns": ["Human review required before any submission."],
        "submission_performed": False,
    }


def create_cold_email_draft(job: Job, matching_skills: str = "Unknown / Not provided") -> dict[str, str]:
    """Create an unsent draft and mark missing recipient information explicitly."""
    company = str(job.get("company", "")).strip() or "Unknown company"
    title = str(job.get("job_title", "")).strip() or "Unknown role"
    body = (
        f"Hello {company} hiring team,\n\n"
        f"I am interested in the {title} opportunity. "
        f"Relevant skills: {matching_skills}.\n\n"
        "I would appreciate the opportunity to learn more about the role.\n\n"
        "Best,\n[Your name]"
    )
    return {
        "recipient": "Needs Contact Research",
        "subject": f"Interest in {title}",
        "body": body,
        "send_performed": "False",
    }