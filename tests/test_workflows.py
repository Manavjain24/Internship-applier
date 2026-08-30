"""Tests for human-controlled workflow helpers."""

from src.application_assistant import create_cold_email_draft, prepare_application
from src.job_analysis import analyze_job
from src.route_discovery import discover_route
from src.tracker import build_followups, dashboard_metrics


def test_unknown_route_never_invents_application_url() -> None:
    result = discover_route({"job_link": "https://loopcv.example/jobs/1"})
    assert result["application_url"] == ""
    assert result["next_action"] == "Manual Review"


def test_analysis_reports_missing_evidence() -> None:
    result = analyze_job({"job_title": "Developer"})
    assert result["match_score"] == "Unknown / Not provided"


def test_followups_and_dashboard_are_derived() -> None:
    rows = [{"company": "Acme", "job_title": "Developer", "application_status": "Applied", "priority": "High Priority", "follow_up_date": "2026-08-30"}]
    assert build_followups(rows)[0]["days_remaining"] == "0"
    assert dashboard_metrics(rows)["applied"] == 1
    assert dashboard_metrics(rows)["high_priority_jobs"] == 1


def test_application_and_email_stop_before_irreversible_actions() -> None:
    job = {"company": "Acme", "job_title": "Developer", "job_link": ""}
    assert prepare_application(job)["submission_performed"] is False
    assert create_cold_email_draft(job)["send_performed"] == "False"