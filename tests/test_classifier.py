"""Tests for title-only job classification."""

from src.classifier import classify_job_title


def test_internship_is_high_priority_and_saved() -> None:
    result = classify_job_title("Software Engineer Intern")
    assert result["priority"] == "High Priority"
    assert result["relevance_score"] == 9
    assert result["application_status"] == "Saved"


def test_senior_role_is_not_applying() -> None:
    result = classify_job_title("Senior Software Engineer")
    assert result["priority"] == "Not Applying"
    assert result["application_status"] == "Not Applying"


def test_engineer_level_three_is_not_applying() -> None:
    result = classify_job_title("Software Engineer III")
    assert result["priority"] == "Not Applying"
