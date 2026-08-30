"""Tests for Google Sheet input helpers."""

import pytest

from src.google_sheets import extract_sheet_id


def test_extract_sheet_id_from_editor_url() -> None:
    url = "https://docs.google.com/spreadsheets/d/sheet-123/edit?gid=0#gid=0"
    assert extract_sheet_id(url) == "sheet-123"


def test_extract_sheet_id_rejects_other_urls() -> None:
    with pytest.raises(ValueError):
        extract_sheet_id("https://example.com/sheet-123")