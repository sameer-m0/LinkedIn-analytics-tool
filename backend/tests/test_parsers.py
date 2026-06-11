from datetime import date

from app.models.upload import UploadType
from app.parsers import registry
from app.parsers.format_detector import SpreadsheetFormat, detect_format


def test_format_detection_xlsx(content_xlsx):
    assert detect_format(content_xlsx) is SpreadsheetFormat.XLSX


def test_followers_autodetect_and_header_offset(followers_xlsx):
    result, wb, conf = registry.parse(followers_xlsx)
    assert result.upload_type is UploadType.FOLLOWERS
    assert conf >= 0.5
    # Header was on row 3; values parsed with locale normalization ("1,234").
    totals = [m for m in result.metrics if m.metric == "total_followers"]
    assert len(totals) == 3
    assert totals[0].metric_date == date(2024, 1, 15)
    assert totals[0].value == 1234.0


def test_visitors_autodetect(visitors_xlsx):
    result, wb, conf = registry.parse(visitors_xlsx)
    assert result.upload_type is UploadType.VISITORS
    metrics = {(m.metric, m.value) for m in result.metrics}
    assert ("page_views", 500.0) in metrics
    assert ("unique_visitors", 320.0) in metrics


def test_content_autodetect_and_derived_rates(content_xlsx):
    result, wb, conf = registry.parse(content_xlsx)
    assert result.upload_type is UploadType.CONTENT
    assert len(result.posts) == 2
    video = next(p for p in result.posts if p.post_type == "video")
    # engagement_rate = (reactions+comments+reposts+clicks)/impressions
    assert abs(video.engagement_rate - (300 + 40 + 15 + 120) / 10000) < 1e-9
    assert abs(video.ctr - 120 / 10000) < 1e-9


def test_manual_override(content_xlsx):
    result, _, _ = registry.parse(content_xlsx, override=UploadType.CONTENT)
    assert result.upload_type is UploadType.CONTENT
