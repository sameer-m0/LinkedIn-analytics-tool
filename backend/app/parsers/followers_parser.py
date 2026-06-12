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
        has_follower_timeseries = False
        has_demographics = False
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if {"organic_followers", "total_followers", "sponsored_followers"} & keys:
                has_follower_timeseries = True
            lowered = {h.strip().lower() for h in sheet.headers}
            if lowered & set(_DEMO_DIMENSIONS):
                has_demographics = True

        if has_follower_timeseries:
            return 0.9
        # Only claim demographic-only workbooks if they do NOT look like a
        # visitors file (which also has Location/Industry/… tabs).  Without a
        # follower time-series sheet the file is not ours.
        return 0.0

    def parse(self, workbook: Workbook) -> ParseResult:
        result = ParseResult(upload_type=self.upload_type)
        # Two passes: parse the follower time-series first so we know the
        # "as of" date, then attach demographics to that snapshot date. This
        # keeps the snapshot deterministic (tied to the data, never the wall
        # clock) so re-uploads dedupe and demographic growth isn't faked.
        demo_sheets = []
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if "date" in keys and (
                {"organic_followers", "total_followers", "sponsored_followers"} & keys
            ):
                self._parse_timeseries(sheet, result)
            else:
                demo_sheets.append(sheet)

        snapshot = max((m.metric_date for m in result.metrics), default=None)
        for sheet in demo_sheets:
            self._parse_demographics(sheet, result, snapshot)
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

    def _parse_demographics(self, sheet, result: ParseResult, snapshot) -> None:
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
        # ``snapshot`` is the latest follower-metric date (deterministic). If the
        # workbook had no time-series at all, skip demographics rather than
        # inventing a wall-clock date that would corrupt growth comparisons.
        if snapshot is None:
            return
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
