"""Parser registry + auto-detection dispatch.

The registry owns the list of available parsers. Auto-detection picks the
highest-confidence parser; a caller may force a specific ``UploadType``
(manual override).
"""
from __future__ import annotations

from app.models.upload import UploadType
from app.parsers.base import BaseParser, ParseResult, Workbook, load_workbook
from app.parsers.content_parser import ContentParser
from app.parsers.followers_parser import FollowersParser
from app.parsers.visitors_parser import VisitorsParser

_PARSERS: dict[UploadType, BaseParser] = {
    UploadType.FOLLOWERS: FollowersParser(),
    UploadType.VISITORS: VisitorsParser(),
    UploadType.CONTENT: ContentParser(),
}

_MIN_CONFIDENCE = 0.5


def detect_type(workbook: Workbook) -> tuple[UploadType, float]:
    """Return the best-matching upload type and its confidence."""
    best_type, best_conf = UploadType.UNKNOWN, 0.0
    for utype, parser in _PARSERS.items():
        conf = parser.confidence(workbook)
        if conf > best_conf:
            best_type, best_conf = utype, conf
    return best_type, best_conf


def parse(data: bytes, *, override: UploadType | None = None) -> tuple[ParseResult, Workbook, float]:
    """Load, (auto-)detect, and parse. Raises ValueError if undetectable."""
    workbook = load_workbook(data)
    if override and override is not UploadType.UNKNOWN:
        utype, confidence = override, _PARSERS[override].confidence(workbook)
    else:
        utype, confidence = detect_type(workbook)
        if utype is UploadType.UNKNOWN or confidence < _MIN_CONFIDENCE:
            raise ValueError(
                "Could not auto-detect export type. Please choose the type manually."
            )
    result = _PARSERS[utype].parse(workbook)
    return result, workbook, confidence
