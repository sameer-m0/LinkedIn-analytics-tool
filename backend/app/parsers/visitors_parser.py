from __future__ import annotations

from app.models.upload import UploadType
from app.parsers.base import BaseParser, MetricRecord, ParseResult, Workbook
from app.parsers.locale import detect_dayfirst, parse_date, parse_number
from app.parsers.synonyms import resolve_header

SOURCE = "visitors"

# Canonical visitor metric keys the dashboard reads.
_METRICS = (
    "page_views",
    "unique_visitors",
    "desktop_page_views",
    "mobile_page_views",
)

# At least one of these must resolve in a sheet for us to claim the workbook.
_DETECTION_KEYS = {"page_views", "unique_visitors"}


class VisitorsParser(BaseParser):
    upload_type = UploadType.VISITORS

    def confidence(self, workbook: Workbook) -> float:
        # A visitors export has page-view / unique-visitor columns and never a
        # follower time series, so this cleanly distinguishes it from followers
        # (both files carry the same demographic tabs).
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if _DETECTION_KEYS & keys:
                return 0.9
        return 0.0

    def parse(self, workbook: Workbook) -> ParseResult:
        result = ParseResult(upload_type=self.upload_type)
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if "date" not in keys or not (_DETECTION_KEYS & keys):
                continue
            date_samples = [str(r.get("date")) for r in sheet.rows[:20] if r.get("date")]
            dayfirst = detect_dayfirst(date_samples)
            present = [m for m in _METRICS if any(m in r for r in sheet.rows)]
            result.detected_headers.setdefault("visitors", []).extend(present)
            for row in sheet.rows:
                d = parse_date(row.get("date"), dayfirst=dayfirst)
                if d is None:
                    continue
                for mk in present:
                    val = parse_number(row.get(mk))
                    if val is not None:
                        result.metrics.append(MetricRecord(d, SOURCE, mk, val))
        return result
