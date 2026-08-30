"""Conservative application-route discovery."""

from urllib.parse import urlparse

from .data_loader import Job


def discover_route(job: Job) -> dict[str, str]:
    """Classify only recognizable source URLs; never invent an application URL."""
    url = str(job.get("job_link", "")).strip()
    host = urlparse(url).netloc.casefold()
    if "linkedin.com" in host:
        return {"application_method": "LinkedIn", "application_url": url, "next_action": "Manual LinkedIn Application Required"}
    if url and host and "loopcv" not in host:
        return {"application_method": "Unknown", "application_url": "", "next_action": "Manual Review"}
    return {"application_method": "Unknown", "application_url": "", "next_action": "Manual Review"}