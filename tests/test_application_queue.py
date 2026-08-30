"""Tests for Application Queue planning."""

from src.application_queue import job_identity, sync_queue_rows


def test_identity_is_stable_and_case_insensitive() -> None:
    assert job_identity({"company": "Acme", "job_title": "Developer", "location": "NY"}) == (
        "acme|developer|ny"
    )


def test_queue_excludes_not_applying_and_preserves_manual_fields() -> None:
    processed = [
        {
            "company": "Acme",
            "job_title": "Developer",
            "location": "NY",
            "priority": "High Priority",
            "relevance_score": "9",
        },
        {
            "company": "Big Co",
            "job_title": "Senior Developer",
            "location": "Remote",
            "priority": "Not Applying",
        },
    ]
    existing = [
        {
            "id": "acme|developer|ny",
            "company": "Acme",
            "job_title": "Developer",
            "location": "NY",
            "application_status": "Applied",
            "date_applied": "2026-08-20",
            "notes": "Submitted manually",
        }
    ]

    new_rows, updated_rows, _ = sync_queue_rows(processed, existing, checked_on="2026-08-30")

    assert new_rows == []
    assert updated_rows[0]["application_status"] == "Applied"
    assert updated_rows[0]["date_applied"] == "2026-08-20"
    assert updated_rows[0]["notes"] == "Submitted manually"
    assert updated_rows[0]["last_checked"] == "2026-08-30"


def test_applied_status_fills_only_an_empty_applied_date() -> None:
    processed = [{"company": "Acme", "job_title": "Developer", "location": "NY", "priority": "High Priority"}]
    existing = [{
        "company": "Acme", "job_title": "Developer", "location": "NY",
        "application_status": "Applied", "date_applied": "",
    }]
    _, updated_rows, _ = sync_queue_rows(processed, existing, checked_on="2026-08-30")
    assert updated_rows[0]["date_applied"] == "2026-08-30"

    existing[0]["date_applied"] = "2026-08-20"
    _, updated_rows, _ = sync_queue_rows(processed, existing, checked_on="2026-08-30")
    assert updated_rows[0]["date_applied"] == "2026-08-20"