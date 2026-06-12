from __future__ import annotations

from datetime import datetime

from app.models.upload import UploadType
from app.parsers.base import BaseParser, MetricRecord, ParseResult, PostRecord, Workbook
from app.parsers.locale import detect_dayfirst, parse_date, parse_number
from app.parsers.synonyms import resolve_header

SOURCE = "content"

# Per-post content columns we care about. Used to score which sheet is the
# richest "all posts" sheet (vs. partial "Top posts (Impressions)" tabs).
_POST_COLS = (
    "impressions", "clicks", "reactions", "comments", "shares",
    "engagement_rate", "ctr", "post_type", "post_title", "posted_at",
)

# Values that are an audience/feed indicator, NOT a media type. LinkedIn exports
# sometimes carry an "Organic/Sponsored" column that must not become post_type.
_NON_POST_TYPES = {"organic", "sponsored", "all", "organic & sponsored", "nan", ""}


class ContentParser(BaseParser):
    upload_type = UploadType.CONTENT

    def confidence(self, workbook: Workbook) -> float:
        score = 0.0
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if "post_url" in keys and "impressions" in keys:
                score = max(score, 0.95)
            elif "impressions" in keys and {"reactions", "comments", "ctr"} & keys:
                score = max(score, 0.7)
        return score

    def parse(self, workbook: Workbook) -> ParseResult:
        result = ParseResult(upload_type=self.upload_type)

        # Separate sheets into "posts" sheets (have a post URL) and daily
        # "metrics" sheets (a date-keyed time series, no per-post URL).
        post_sheets = []
        metric_sheets = []
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if "post_url" in keys:
                post_sheets.append(sheet)
            elif "impressions" in keys and "date" in keys:
                metric_sheets.append(sheet)

        # Parse ONLY the richest posts sheet. Multiple "Top posts (…)" tabs
        # carry partial columns; parsing them all would overwrite good rows with
        # sparse ones during dedupe.
        best_sheet = self._richest_posts_sheet(post_sheets)
        if best_sheet is not None:
            self._parse_posts(best_sheet, result)

        for sheet in metric_sheets:
            self._parse_daily_metrics(sheet, result)

        # Fall back: if there were no dedicated daily-metrics sheets, synthesise
        # the content time series from the posts we parsed.
        if not metric_sheets and result.posts:
            self._metrics_from_posts(result)

        result.metrics = _aggregate_daily(result.metrics)
        return result

    @staticmethod
    def _richest_posts_sheet(sheets):
        best, best_score = None, -1
        for sheet in sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            score = len([k for k in keys if k in _POST_COLS]) * 1000 + len(sheet.rows)
            if score > best_score:
                best, best_score = sheet, score
        return best

    def _parse_posts(self, sheet, result: ParseResult) -> None:
        date_samples = [
            str(r.get("posted_at") or r.get("date"))
            for r in sheet.rows[:20]
            if r.get("posted_at") or r.get("date")
        ]
        dayfirst = detect_dayfirst(date_samples)
        keys = {resolve_header(h) for h in sheet.headers}
        result.detected_headers.setdefault("content", []).extend(sorted(k for k in keys if k))

        for row in sheet.rows:
            url = row.get("post_url")
            if not url:
                continue
            impressions = int(parse_number(row.get("impressions")) or 0)
            posted = parse_date(row.get("posted_at") or row.get("date"), dayfirst=dayfirst)
            posted_dt = datetime(posted.year, posted.month, posted.day) if posted else None

            reactions = int(parse_number(row.get("reactions")) or 0)
            comments = int(parse_number(row.get("comments")) or 0)
            reposts = int(parse_number(row.get("shares")) or 0)
            clicks = int(parse_number(row.get("clicks")) or 0)

            # Prefer the export's own engagement rate / CTR; only derive when
            # absent. Derived values are sanity-clamped to [0, 1].
            er = parse_number(row.get("engagement_rate"))
            if er is None and impressions > 0:
                er = (reactions + comments + reposts + clicks) / impressions
            ctr = parse_number(row.get("ctr"))
            if ctr is None and impressions > 0:
                ctr = clicks / impressions
            er = _clamp_rate(er)
            ctr = _clamp_rate(ctr)

            result.posts.append(
                PostRecord(
                    post_url=str(url).strip(),
                    posted_at=posted_dt,
                    post_type=_clean_post_type(row.get("post_type")),
                    title=_clean_text(row.get("post_title")),
                    impressions=impressions,
                    clicks=clicks,
                    reactions=reactions,
                    comments=comments,
                    reposts=reposts,
                    engagement_rate=er,
                    ctr=ctr,
                )
            )

    def _parse_daily_metrics(self, sheet, result: ParseResult) -> None:
        date_samples = [str(r.get("date")) for r in sheet.rows[:20] if r.get("date")]
        dayfirst = detect_dayfirst(date_samples)
        present = [m for m in ("impressions", "clicks", "reactions", "comments", "shares", "engagement_rate")
                   if any(m in r for r in sheet.rows)]
        for row in sheet.rows:
            d = parse_date(row.get("date"), dayfirst=dayfirst)
            if d is None:
                continue
            for mk in present:
                val = parse_number(row.get(mk))
                if val is None:
                    continue
                if mk == "engagement_rate":
                    val = _clamp_rate(val)
                result.metrics.append(MetricRecord(d, SOURCE, mk, val))

    @staticmethod
    def _metrics_from_posts(result: ParseResult) -> None:
        for p in result.posts:
            if not p.posted_at:
                continue
            d = p.posted_at.date()
            result.metrics.append(MetricRecord(d, SOURCE, "impressions", p.impressions))
            if p.engagement_rate is not None:
                result.metrics.append(MetricRecord(d, SOURCE, "engagement_rate", p.engagement_rate))


def _clean_text(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s and s.lower() != "nan" else None


def _clean_post_type(value) -> str | None:
    s = _clean_text(value)
    if s is None or s.lower() in _NON_POST_TYPES:
        return None
    return s


def _clamp_rate(value: float | None) -> float | None:
    """Engagement rate / CTR are fractions in [0, 1]. Drop impossible values."""
    if value is None:
        return None
    if value < 0:
        return None
    # Some exports give percentages already divided (0.05) — keep. Anything wildly
    # above 1 (>100%) is a parse/alignment artefact, so cap at 1.0.
    return min(value, 1.0)


def _aggregate_daily(metrics: list[MetricRecord]) -> list[MetricRecord]:
    buckets: dict[tuple, list[float]] = {}
    for m in metrics:
        buckets.setdefault((m.metric_date, m.metric), []).append(m.value)
    out: list[MetricRecord] = []
    for (d, metric), vals in buckets.items():
        value = sum(vals) / len(vals) if metric == "engagement_rate" else sum(vals)
        out.append(MetricRecord(d, SOURCE, metric, value))
    return out
