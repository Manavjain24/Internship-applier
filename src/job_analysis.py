"""Evidence-based job analysis helpers."""

from .data_loader import Job


def analyze_job(job: Job, profile: dict[str, str] | None = None) -> dict[str, str]:
    """Compare available job text to an optional profile without inventing facts."""
    description = str(job.get("job_description", "")).strip()
    if not description or not profile:
        return {
            "match_score": "Unknown / Not provided",
            "matching_skills": "Unknown / Not provided",
            "missing_skills": "Unknown / Not provided",
            "relevant_experience": "Unknown / Not provided",
            "potential_concerns": "Job description or profile is unavailable.",
            "recommended_resume": "Unknown / Not provided",
            "application_recommendation": "Possible Match",
        }
    profile_text = " ".join(str(value).casefold() for value in profile.values())
    words = {word.strip(".,:;()[]") for word in description.casefold().split()}
    matching = sorted(word for word in words if len(word) > 2 and word in profile_text)
    return {
        "match_score": str(min(10, len(matching))),
        "matching_skills": ", ".join(matching) or "Unknown / Not provided",
        "missing_skills": "Unknown / Not provided",
        "relevant_experience": "Provided profile information only; verify manually.",
        "potential_concerns": "Review requirements manually.",
        "recommended_resume": "Unknown / Not provided",
        "application_recommendation": "Good Match" if matching else "Possible Match",
    }