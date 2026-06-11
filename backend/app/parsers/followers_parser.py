from __future__ import annotations

from app.models.demographic import DemographicDimension
from app.models.upload import UploadType
from app.parsers.base import (
    BaseParser,
    DemographicRecord,
    MetricRecord,
    ParseResult,
    Workbook,
)
from app.parsers.locale import detect_dayfirst, parse_date, parse_number
from app.parsers.synonyms import resolve_header

SOURCE = "followers"

# Header text (normalized) -> demographic dimension for the demographic tabs.
_DEMO_DIMENSIONS = {
    "job function": DemographicDimension.JOB_FUNCTION,
    "seniority": DemographicDimension.SENIORITY,
    "industry": DemographicDimension.INDUSTRY,
    "location": DemographicDimension.LOCATION,
    "company size": DemographicDimension.COMPANY_SIZE,
}


class FollowersParser(BaseParser):
    upload_type = UploadType.FOLLOWERS

    def confidence(self, workbook: Workbook) -> float:
        score = 0.0
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if {"organic_followers", "total_followers", "sponsored_followers"} & keys:
                score = max(score, 0.9)
            lowered = {h.strip().lower() for h in sheet.headers}
            if lowered & set(_DEMO_DIMENSIONS):
                score = max(score, 0.6)
        return score

    def parse(self, workbook: Workbook) -> ParseResult:
        result = ParseResult(upload_type=self.upload_type)
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if "date" in keys and (
                {"organic_followers", "total_followers", "sponsored_followers"} & keys
            ):
                self._parse_timeseries(sheet, result)
            else:
                self._parse_demographics(sheet, result)
        return result

    def _parse_timeseries(self, sheet, result: ParseResult) -> None:
        date_samples = [str(r.get("date")) for r in sheet.rows[:20] if r.get("date")]
        dayfirst = detect_dayfirst(date_samples)
        metric_keys = [
            k for k in ("organic_followers", "sponsored_followers", "total_followers")
            if any(k in r for r in sheet.rows)
        ]
        result.detected_headers.setdefault("followers", []).extend(metric_keys)
        for row in sheet.rows:
            d = parse_date(row.get("date"), dayfirst=dayfirst)
            if d is None:
                continue
            for mk in metric_keys:
                val = parse_number(row.get(mk))
                if val is not None:
                    result.metrics.append(MetricRecord(d, SOURCE, mk, val))

    def _parse_demographics(self, sheet, result: ParseResult) -> None:
        # Find the category column (one of the dimension headers) and the count column.
        dim = None
        cat_key = None
        for h in sheet.headers:
            if h.strip().lower() in _DEMO_DIMENSIONS:
                dim = _DEMO_DIMENSIONS[h.strip().lower()]
                cat_key = f"__raw__{h}"
                break
        if dim is None:
            return
        # Use the most recent metric date as the snapshot date; fall back to today-less data.
        from datetime import date as _date

        snapshot = max(
            (m.metric_date for m in result.metrics), default=_date.today()
        )
        result.detected_headers.setdefault("demographics", []).append(dim.value)
        for row in sheet.rows:
            category = row.get(cat_key) or row.get("demographic_category")
            count = parse_number(row.get("follower_count") or row.get("total_followers"))
            if category is None or count is None:
                # Count column may be the only other numeric column present.
                count = count if count is not None else _first_number(row)
            if category is None or count is None:
                continue
            result.demographics.append(
                DemographicRecord(snapshot, dim, str(category).strip(), count)
            )


def _first_number(row: dict) -> float | None:
    for v in row.values():
        n = parse_number(v)
        if n is not None:
            return n
    return None
