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


def test_content_media_type_synonyms_and_heuristics():
    from tests.conftest import build_xlsx
    xlsx = build_xlsx([
        ["Post URL", "Post type", "Content Type", "Created date", "Impressions", "Clicks", "Reactions", "Comments", "Shares", "Post title", "Views"],
        ["https://linkedin.com/p/1", "organic", "document", "01/15/2024", "100", "5", "5", "2", "1", "Some post title", "0"],
        ["https://linkedin.com/p/2", None, None, "01/16/2024", "200", "1", "1", "0", "0", "Read our latest PDF slide carousel guide.", "0"],
        ["https://linkedin.com/p/3", None, None, "01/17/2024", "300", "2", "2", "1", "0", "Watch this cool footage.", "10"],
    ])
    result, wb, conf = registry.parse(xlsx)
    assert result.upload_type is UploadType.CONTENT
    assert len(result.posts) == 3
    
    p1 = next(p for p in result.posts if p.post_url == "https://linkedin.com/p/1")
    p2 = next(p for p in result.posts if p.post_url == "https://linkedin.com/p/2")
    p3 = next(p for p in result.posts if p.post_url == "https://linkedin.com/p/3")
    
    assert p1.post_type == "document"
    assert p2.post_type == "document"
    assert p3.post_type == "video"

