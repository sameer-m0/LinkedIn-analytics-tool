"""Column-synonym resolution.

LinkedIn renames columns across export versions/locales. We map raw header
text to canonical field keys. Adding a future synonym is a one-line edit to
``SYNONYMS`` — that is the entire extensibility surface (Open/Closed).
"""
from __future__ import annotations

import re

# canonical_key -> list of accepted header variants (matched case/space-insensitively)
SYNONYMS: dict[str, list[str]] = {
    # --- shared / dates ---
    "date": ["date", "day"],
    # --- followers ---
    "organic_followers": ["organic followers", "new followers (organic)", "organic"],
    "sponsored_followers": ["sponsored followers", "new followers (sponsored)", "sponsored"],
    "total_followers": ["total followers", "total new followers", "new followers", "followers"],
    # --- visitors ---
    "page_views": ["page views (total)", "total page views", "page views", "overview page views"],
    "unique_visitors": [
        "unique visitors (total)",
        "total unique visitors",
        "unique visitors",
    ],
    "desktop_page_views": ["desktop page views", "page views (desktop)"],
    "mobile_page_views": ["mobile page views", "page views (mobile)"],
    # --- content / posts ---
    "post_url": ["post url", "post link", "url", "link"],
    "post_title": ["post title", "title", "content", "post"],
    "post_type": ["post type", "content type", "type", "media type"],
    "posted_at": ["created date", "posted date", "date posted", "publish date"],
    "impressions": ["impressions", "impressions (organic)", "impressions (total)"],
    "clicks": ["clicks", "clicks (total)", "post clicks"],
    "reactions": ["reactions", "likes", "reactions (total)"],
    "comments": ["comments", "comments (total)"],
    "shares": ["shares", "reposts"],
    "engagement_rate": ["engagement rate", "engagement_rate", "engagement"],
    "ctr": ["click through rate (ctr)", "click-through rate", "ctr"],
    # Note: demographic category columns (Job function, Seniority, …) are
    # intentionally NOT mapped here — they collide with metric names. The
    # followers parser reads them directly from the raw (unmapped) columns so
    # the count column ("Total followers") still resolves to ``total_followers``.
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


# Pre-built reverse index: normalized-variant -> canonical key.
# First definition wins so earlier (more specific) canonicals are not clobbered
# by a later canonical that lists the same variant.
_REVERSE: dict[str, str] = {}
for _canon, _variants in SYNONYMS.items():
    for _v in _variants:
        _REVERSE.setdefault(_normalize(_v), _canon)


def resolve_header(raw_header: str) -> str | None:
    """Return the canonical key for a raw header, or None if unknown."""
    return _REVERSE.get(_normalize(raw_header))


def map_headers(headers: list[str]) -> dict[int, str]:
    """Map column index -> canonical key for every recognized header."""
    mapping: dict[int, str] = {}
    for idx, h in enumerate(headers):
        canon = resolve_header(h)
        if canon is not None:
            mapping[idx] = canon
    return mapping
