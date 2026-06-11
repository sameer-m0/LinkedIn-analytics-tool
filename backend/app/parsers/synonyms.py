"""Column-synonym resolution.

LinkedIn renames columns across export versions/locales. We map raw header
text to canonical field keys. Adding a future synonym is a one-line edit to
``SYNONYMS`` — that is the entire extensibility surface (Open/Closed).
"""
from __future__ import annotations

import re

# canonical_key -> list of accepted header variants (matched case/space-insensitively)
# PRIORITY: within each list, earlier entries win when multiple columns
# resolve to the same canonical key in one sheet.  Always put the most
# specific / "(total)" variant BEFORE "(organic)" so totals are preferred.
SYNONYMS: dict[str, list[str]] = {
    # --- shared / dates ---
    "date": ["date", "day"],
    # --- followers ---
    "organic_followers": ["organic followers", "new followers (organic)", "organic"],
    "sponsored_followers": ["sponsored followers", "new followers (sponsored)", "sponsored"],
    "total_followers": ["total followers", "total new followers", "new followers", "followers"],
    # --- visitors (overview) ---
    "page_views": [
        "overview page views (total)",
        "page views (total)",
        "total page views",
        "page views",
        "overview page views",
    ],
    "unique_visitors": [
        "overview unique visitors (total)",
        "unique visitors (total)",
        "total unique visitors",
        "unique visitors",
    ],
    "desktop_page_views": [
        "overview page views (desktop)",
        "desktop page views",
        "page views (desktop)",
    ],
    "mobile_page_views": [
        "overview page views (mobile)",
        "mobile page views",
        "page views (mobile)",
    ],
    "desktop_unique_visitors": [
        "overview unique visitors (desktop)",
        "unique visitors (desktop)",
    ],
    "mobile_unique_visitors": [
        "overview unique visitors (mobile)",
        "unique visitors (mobile)",
    ],
    # --- visitors (total / all-section page views) ---
    "total_page_views": [
        "total page views (total)",
        "total page views (desktop)",
        "total page views (mobile)",
    ],
    "total_unique_visitors": [
        "total unique visitors (total)",
        "total unique visitors (desktop)",
        "total unique visitors (mobile)",
    ],
    # --- visitors (life tab) ---
    "life_page_views": [
        "life page views (total)",
        "life page views (desktop)",
        "life page views (mobile)",
    ],
    "life_unique_visitors": [
        "life unique visitors (total)",
        "life unique visitors (desktop)",
        "life unique visitors (mobile)",
    ],
    # --- visitors (jobs tab) ---
    "jobs_page_views": [
        "jobs page views (total)",
        "jobs page views (desktop)",
        "jobs page views (mobile)",
    ],
    "jobs_unique_visitors": [
        "jobs unique visitors (total)",
        "jobs unique visitors (desktop)",
        "jobs unique visitors (mobile)",
    ],
    # --- content / posts ---
    "post_url": ["post url", "post link", "url", "link"],
    "post_title": ["post title", "title", "content", "post"],
    "post_type": ["post type", "content type", "type", "media type"],
    "posted_at": ["created date", "posted date", "date posted", "publish date"],
    # NOTE: "(total)" BEFORE "(organic)" so we prefer total when both exist
    "impressions": ["impressions", "impressions (total)", "impressions (organic)"],
    "clicks": ["clicks", "clicks (total)", "clicks (organic)", "post clicks"],
    "reactions": ["reactions", "reactions (total)", "reactions (organic)", "likes"],
    "comments": ["comments", "comments (total)", "comments (organic)"],
    "shares": ["shares", "reposts", "reposts (total)", "reposts (organic)"],
    "engagement_rate": [
        "engagement rate",
        "engagement_rate",
        "engagement rate (total)",
        "engagement rate (organic)",
        "engagement",
    ],
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
    """Map column index -> canonical key for every recognized header.

    If multiple headers resolve to the same canonical key in the same sheet,
    we resolve the collision by preferring the synonym that appears earlier
    in the SYNONYMS definition list (higher priority).
    """
    candidates: dict[str, list[tuple[int, int]]] = {}

    for idx, h in enumerate(headers):
        canon = resolve_header(h)
        if canon is not None:
            normalized_h = _normalize(h)
            priority = 999
            for priority_idx, variant in enumerate(SYNONYMS[canon]):
                if _normalize(variant) == normalized_h:
                    priority = priority_idx
                    break
            candidates.setdefault(canon, []).append((idx, priority))

    mapping: dict[int, str] = {}
    for canon, idx_priorities in candidates.items():
        idx_priorities.sort(key=lambda x: x[1])
        best_idx = idx_priorities[0][0]
        mapping[best_idx] = canon

    return mapping
