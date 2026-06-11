"""Shared fixtures: in-memory Excel builders used by parser/API tests."""
from __future__ import annotations

import io

import openpyxl
import pytest


def build_xlsx(rows: list[list], *, sheet_name: str = "Sheet1") -> bytes:
    """Create an .xlsx workbook from raw rows (list of lists)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def followers_xlsx() -> bytes:
    # Two metadata rows before the real header (header not on row 1).
    return build_xlsx(
        [
            ["Follower analytics for Acme", None],
            ["Exported 2024-03-01", None],
            ["Date", "Total followers"],
            ["01/15/2024", "1,234"],
            ["01/16/2024", "1,250"],
            ["01/17/2024", "1,275"],
        ]
    )


@pytest.fixture
def visitors_xlsx() -> bytes:
    return build_xlsx(
        [
            ["Date", "Total page views", "Total unique visitors", "Desktop page views", "Mobile page views"],
            ["01/15/2024", "500", "320", "300", "200"],
            ["01/16/2024", "540", "350", "320", "220"],
        ]
    )


@pytest.fixture
def content_xlsx() -> bytes:
    return build_xlsx(
        [
            ["Post URL", "Post type", "Created date", "Impressions", "Clicks", "Reactions", "Comments", "Reposts"],
            ["https://linkedin.com/p/1", "video", "01/15/2024", "10000", "120", "300", "40", "15"],
            ["https://linkedin.com/p/2", "image", "01/16/2024", "8000", "50", "120", "10", "5"],
        ]
    )
