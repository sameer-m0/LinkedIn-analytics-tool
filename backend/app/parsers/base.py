"""Parser framework: workbook loading + the ``BaseParser`` contract.

Design (SOLID):
  * Single Responsibility — loading, detection, and per-type parsing are split.
  * Open/Closed — new export types are new ``BaseParser`` subclasses; the
    registry discovers them without edits to ingestion.
  * Liskov — every parser returns the same ``ParseResult`` shape.
"""
from __future__ import annotations

import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd

from app.models.demographic import DemographicDimension
from app.models.upload import UploadType
from app.parsers.format_detector import SpreadsheetFormat, detect_format
from app.parsers.header_detector import HeaderDetection, detect_header
from app.parsers.synonyms import map_headers


@dataclass
class Sheet:
    """A single worksheet, already trimmed to its detected header + data."""

    name: str
    headers: list[str]
    rows: list[dict[str, object]]  # canonical_key -> raw cell value
    detection: HeaderDetection


@dataclass
class Workbook:
    fmt: SpreadsheetFormat
    sheets: list[Sheet]


# --- Output records (parser-agnostic, consumed by the ingestion pipeline) ---


@dataclass
class MetricRecord:
    metric_date: date
    source: str
    metric: str
    value: float


@dataclass
class PostRecord:
    post_url: str
    posted_at: datetime | None
    post_type: str | None
    title: str | None
    impressions: int
    clicks: int
    reactions: int
    comments: int
    reposts: int
    engagement_rate: float | None
    ctr: float | None


@dataclass
class DemographicRecord:
    snapshot_date: date
    dimension: DemographicDimension
    category: str
    value: float


@dataclass
class ParseResult:
    upload_type: UploadType
    metrics: list[MetricRecord] = field(default_factory=list)
    posts: list[PostRecord] = field(default_factory=list)
    demographics: list[DemographicRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    detected_headers: dict[str, list[str]] = field(default_factory=dict)
    # Raw header row found per sheet — surfaced in the upload report purely as a
    # diagnostic so the real LinkedIn column names are visible without re-parsing.
    sheet_headers: dict[str, list[str]] = field(default_factory=dict)

    @property
    def total_rows(self) -> int:
        return len(self.metrics) + len(self.posts) + len(self.demographics)


def load_workbook(data: bytes) -> Workbook:
    """Read raw bytes into a ``Workbook`` with per-sheet header detection."""
    fmt = detect_format(data)
    engine = fmt.engine or "openpyxl"
    raw_sheets = pd.read_excel(io.BytesIO(data), sheet_name=None, header=None, engine=engine)

    sheets: list[Sheet] = []
    for name, raw_df in raw_sheets.items():
        if raw_df.empty:
            continue
        detection = detect_header(raw_df)
        body = raw_df.iloc[detection.header_row + 1 :].reset_index(drop=True)
        col_map = map_headers(detection.headers)

        rows: list[dict[str, object]] = []
        for _, series in body.iterrows():
            values = list(series.values)
            record: dict[str, object] = {}
            for idx, canon in col_map.items():
                if idx < len(values):
                    record[canon] = values[idx]
            # Keep raw unmapped columns too (keyed by original header) so
            # demographic parsing can read arbitrary category columns.
            for idx, raw_header in enumerate(detection.headers):
                if idx not in col_map and idx < len(values):
                    record.setdefault(f"__raw__{raw_header}", values[idx])
            if any(v is not None and str(v).strip() and not pd.isna(v) for v in record.values()):
                rows.append(record)

        sheets.append(Sheet(name=str(name), headers=detection.headers, rows=rows, detection=detection))

    return Workbook(fmt=fmt, sheets=sheets)


class BaseParser(ABC):
    """Contract every export parser implements."""

    upload_type: UploadType

    @abstractmethod
    def confidence(self, workbook: Workbook) -> float:
        """Return 0..1 likelihood this parser handles the workbook (auto-detect)."""

    @abstractmethod
    def parse(self, workbook: Workbook) -> ParseResult:
        """Parse the workbook into a ``ParseResult``."""
