from __future__ import annotations

from datetime import datetime

from app.models.upload import UploadType
from app.parsers.base import BaseParser, MetricRecord, ParseResult, PostRecord, Workbook
from app.parsers.locale import detect_dayfirst, parse_date, parse_number
from app.parsers.synonyms import resolve_header

SOURCE = "content"


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
        for sheet in workbook.sheets:
            keys = {resolve_header(h) for h in sheet.headers}
            if "impressions" not in keys:
                continue
            date_samples = [
                str(r.get("posted_at") or r.get("date"))
                for r in sheet.rows[:20]
                if r.get("posted_at") or r.get("date")
            ]
            dayfirst = detect_dayfirst(date_samples)
            result.detected_headers.setdefault("content", []).extend(sorted(k for k in keys if k))

            is_posts_sheet = "post_url" in keys

            for i, row in enumerate(sheet.rows):
                impressions = int(parse_number(row.get("impressions")) or 0)
                url = row.get("post_url")
                posted = parse_date(row.get("posted_at") or row.get("date"), dayfirst=dayfirst)
                posted_dt = datetime(posted.year, posted.month, posted.day) if posted else None

                reactions = int(parse_number(row.get("reactions")) or 0)
                comments = int(parse_number(row.get("comments")) or 0)
                reposts = int(parse_number(row.get("shares")) or 0)
                clicks = int(parse_number(row.get("clicks")) or 0)

                er = parse_number(row.get("engagement_rate"))
                if er is None and impressions > 0:
                    er = (reactions + comments + reposts + clicks) / impressions
                ctr = parse_number(row.get("ctr"))
                if ctr is None and impressions > 0:
                    ctr = clicks / impressions

                if is_posts_sheet:
                    if url:
                        result.posts.append(
                            PostRecord(
                                post_url=str(url).strip(),
                                posted_at=posted_dt,
                                post_type=(str(row["post_type"]).strip() if row.get("post_type") and str(row["post_type"]).strip().lower() != "nan" else None),
                                title=(str(row["post_title"]).strip() if row.get("post_title") and str(row["post_title"]).strip().lower() != "nan" else None),
                                impressions=impressions,
                                clicks=clicks,
                                reactions=reactions,
                                comments=comments,
                                reposts=reposts,
                                engagement_rate=er,
                                ctr=ctr,
                            )
                        )
                else:
                    # Also emit daily impression/engagement metrics for the content time series.
                    if posted:
                        result.metrics.append(MetricRecord(posted, SOURCE, "impressions", impressions))
                        if er is not None:
                            result.metrics.append(
                                MetricRecord(posted, SOURCE, "engagement_rate", er)
                            )
        # Collapse duplicate (date, metric) by summing impressions / averaging rates.
        result.metrics = _aggregate_daily(result.metrics)
        return result


def _aggregate_daily(metrics: list[MetricRecord]) -> list[MetricRecord]:
    buckets: dict[tuple, list[float]] = {}
    for m in metrics:
        buckets.setdefault((m.metric_date, m.metric), []).append(m.value)
    out: list[MetricRecord] = []
    for (d, metric), vals in buckets.items():
        value = sum(vals) if metric == "impressions" else sum(vals) / len(vals)
        out.append(MetricRecord(d, SOURCE, metric, value))
    return out
