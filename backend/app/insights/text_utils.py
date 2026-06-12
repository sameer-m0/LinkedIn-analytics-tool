"""Lightweight, deterministic text analysis of LinkedIn post bodies.

LinkedIn post text (stored in ``Post.title``) frequently uses "fancy" Unicode
(mathematical bold/italic) for emphasis and embeds hashtags + @-style mentions.
Everything here NFKC-normalizes first so ``𝗴𝗮𝗺𝗶𝗻𝗴`` → ``gaming`` before any
extraction. No ML — pure regex/heuristics so results are reproducible and
unit-testable.
"""
from __future__ import annotations

import re
import unicodedata

# A compact English stop-word list — enough to surface meaningful topic words.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "of", "to", "in",
    "on", "for", "with", "at", "by", "from", "up", "out", "as", "is", "are",
    "was", "were", "be", "been", "being", "it", "its", "this", "that", "these",
    "those", "we", "our", "us", "you", "your", "they", "their", "them", "he",
    "she", "his", "her", "i", "me", "my", "what", "which", "who", "whom",
    "how", "when", "where", "why", "all", "each", "more", "most", "other",
    "some", "such", "no", "not", "only", "own", "same", "than", "too", "very",
    "can", "will", "just", "into", "about", "over", "after", "before", "here",
    "there", "have", "has", "had", "do", "does", "did", "now", "also", "one",
    "two", "many", "much", "still", "yet", "even", "every", "any", "because",
    "while", "during", "between", "through", "make", "made", "get", "got",
}

_HASHTAG_RE = re.compile(r"#(\w[\w’']*)", re.UNICODE)
_MENTION_RE = re.compile(r"@(\w[\w.\-]*)", re.UNICODE)
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z’'&-]+", re.UNICODE)
_URL_RE = re.compile(r"https?://\S+|lnkd\.in/\S+", re.IGNORECASE)
# Recurring brand / proper-noun phrases (Title-case or CamelCase tokens).
_PROPER_RE = re.compile(r"\b([A-Z][a-zA-Z]+(?:[A-Z][a-zA-Z]+)?)\b")


def normalize(text: str | None) -> str:
    """NFKC-normalize so styled Unicode collapses to plain ASCII letters."""
    if not text:
        return ""
    return unicodedata.normalize("NFKC", str(text))


def extract_hashtags(text: str | None) -> list[str]:
    """Return lowercase hashtags (without '#'), de-duplicated, order-preserving."""
    norm = normalize(text)
    seen: dict[str, None] = {}
    for tag in _HASHTAG_RE.findall(norm):
        seen.setdefault(tag.lower(), None)
    return list(seen)


def extract_mentions(text: str | None) -> list[str]:
    """Return @-style mentions (without '@'). LinkedIn exports rarely keep these."""
    norm = normalize(text)
    seen: dict[str, None] = {}
    for m in _MENTION_RE.findall(norm):
        seen.setdefault(m, None)
    return list(seen)


def extract_brands(text: str | None, *, ignore: set[str] | None = None) -> list[str]:
    """Heuristic brand/entity extraction when @-mentions are absent.

    Picks recurring Title-case / CamelCase tokens (e.g. ``PlaySuper``, ``Forbes``)
    from the *first portion* of the post, skipping the hashtag block and common
    sentence-start words. Best-effort — used only to suggest who to tag.
    """
    ignore = ignore or set()
    norm = normalize(text)
    # Drop URLs and hashtags so we don't pick fragments out of them.
    norm = _URL_RE.sub(" ", _HASHTAG_RE.sub(" ", norm))
    out: dict[str, None] = {}
    for token in _PROPER_RE.findall(norm):
        low = token.lower()
        if low in _STOPWORDS or low in ignore or len(token) < 3:
            continue
        # CamelCase (PlaySuper) or known multi-cap are strong brand signals; a
        # plain Title-case word is weaker but still useful when it recurs.
        out.setdefault(token, None)
    return list(out)


def extract_keywords(text: str | None, *, limit: int = 8) -> list[str]:
    """Most frequent meaningful (non-stopword) lowercase words."""
    norm = normalize(text).lower()
    norm = _URL_RE.sub(" ", norm)
    freq: dict[str, int] = {}
    for w in _WORD_RE.findall(norm):
        w = w.strip("'’-&")
        if len(w) < 3 or w in _STOPWORDS:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def char_length(text: str | None) -> int:
    return len(normalize(text))


def has_link(text: str | None) -> bool:
    return bool(_URL_RE.search(normalize(text)))


def has_question(text: str | None) -> bool:
    return "?" in normalize(text)


def hook(text: str | None, *, max_chars: int = 90) -> str:
    """First line / opening sentence — the 'hook' shown before 'see more'."""
    norm = normalize(text).strip()
    if not norm:
        return ""
    first = norm.splitlines()[0].strip()
    return first if len(first) <= max_chars else first[: max_chars - 1].rstrip() + "…"
