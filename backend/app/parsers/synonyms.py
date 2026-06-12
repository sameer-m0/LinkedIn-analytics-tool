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
    # --- visitors ---
    # The LinkedIn Visitors export has many section columns (Overview / Life /
    # Jobs / People / Products), each split Desktop/Mobile/Total, plus an
    # all-section "Total page views (Total)" / "Total unique visitors (Total)".
    # We collapse the meaningful top-line + device split into the four canonical
    # keys the dashboard reads. Priority order: all-section total first, then
    # overview, then bare. Section-specific tabs are intentionally ignored.
    "page_views": [
        "total page views (total)",
        "page views (total)",
        "overview page views (total)",
        "total page views",
        "page views",
        "overview page views",
    ],
    "unique_visitors": [
        "total unique visitors (total)",
        "unique visitors (total)",
        "overview unique visitors (total)",
        "total unique visitors",
        "unique visitors",
    ],
    "desktop_page_views": [
        "total page views (desktop)",
        "overview page views (desktop)",
        "desktop page views",
        "page views (desktop)",
    ],
    "mobile_page_views": [
        "total page views (mobile)",
        "overview page views (mobile)",
        "mobile page views",
        "page views (mobile)",
    ],
    # --- content / posts ---
    # NOTE: keep these specific. Greedy variants like bare "type"/"content"/
    # "post" previously matched the wrong columns and shifted post data.
    "post_url": ["post url", "post link", "url", "link"],
    "post_title": ["post title", "share commentary", "title"],
    "post_type": ["post type", "media type", "content type"],
    "posted_at": ["created date", "posted date", "date posted", "publish date", "post date", "date published"],
    # "(total)" BEFORE "(organic)"/"(sponsored)" so totals win when several exist.
    "impressions": ["impressions (total)", "impressions", "impressions (organic)", "impressions (sponsored)"],
    "clicks": ["clicks (total)", "clicks", "clicks (organic)", "clicks (sponsored)", "post clicks"],
    "reactions": ["reactions (total)", "reactions", "reactions (organic)", "reactions (sponsored)", "likes"],
    "comments": ["comments (total)", "comments", "comments (organic)", "comments (sponsored)"],
    "shares": ["reposts (total)", "reposts", "shares", "reposts (organic)", "reposts (sponsored)"],
    "engagement_rate": [
        "engagement rate (total)",
        "engagement rate",
        "engagement_rate",
        "engagement rate (organic)",
        "engagement rate (sponsored)",
    ],
    "ctr": ["click through rate (ctr)", "click-through rate (ctr)", "click-through rate", "ctr"],
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
