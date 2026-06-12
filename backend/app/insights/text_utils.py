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
# A capitalized name token, e.g. "Mohit", "PlaySuper", "O'Brien".
_NAME_TOKEN_RE = re.compile(r"[A-Z][a-zA-Z'’.&]+")
_NAME_SEP_RE = re.compile(r"[|•·/,]+")
_SENTENCE_PUNCT_RE = re.compile(r"[.?!:;]")
# Words that look capitalized at a line start but aren't names.
_NON_NAME_WORDS = {
    "the", "a", "we", "our", "us", "you", "your", "they", "i", "and", "to",
    "follow", "thanks", "thank", "featuring", "with", "read", "more", "here",
    "shoutout", "ps", "join", "meet", "from", "by", "via", "credits", "credit",
}


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


def _is_name_line(line: str) -> bool:
    """A line that is (almost) entirely capitalized name tokens + separators.

    LinkedIn renders @-tagged people as their display names, usually grouped on
    the last line(s) before the hashtags, e.g. "Mohit Mohan | Disha Sharma".
    """
    cleaned = _NAME_SEP_RE.sub(" ", line).strip()
    if not cleaned or _SENTENCE_PUNCT_RE.search(cleaned):
        return False
    words = cleaned.split()
    if len(words) < 2 or len(words) > 14:
        return False
    name_like = sum(1 for w in words if _NAME_TOKEN_RE.fullmatch(w) and w.lower() not in _NON_NAME_WORDS)
    return name_like >= 2 and name_like / len(words) >= 0.8


def _pair_names(line: str) -> list[str]:
    """Pair consecutive capitalized tokens into "First Last" names."""
    cleaned = _NAME_SEP_RE.sub(" ", line)
    tokens = [
        t for t in _NAME_TOKEN_RE.findall(cleaned)
        if t.lower() not in _NON_NAME_WORDS and len(t) > 1
    ]
    names: list[str] = []
    i = 0
    while i < len(tokens):
        if i + 1 < len(tokens):
            names.append(f"{tokens[i]} {tokens[i + 1]}")
            i += 2
        else:
            names.append(tokens[i])
            i += 1
    return names


def extract_tagged_people(text: str | None) -> list[str]:
    """Extract tagged people from the mention block above the hashtags.

    Looks at the last few non-empty lines before the first hashtag (where
    LinkedIn places @-tags), keeps the ones that read as name lists, and pairs
    tokens into full names. Returns [] when no such block is present.
    """
    norm = normalize(text)
    if not norm:
        return []
    lines = [ln.strip() for ln in norm.splitlines()]
    cut = next((i for i, ln in enumerate(lines) if "#" in ln), len(lines))
    region = [ln for ln in lines[:cut] if ln]

    names: list[str] = []
    # Scan the tail of the region; collect consecutive name lines.
    for ln in reversed(region[-4:]):
        if _is_name_line(ln):
            names = _pair_names(ln) + names
        elif names:
            break  # passed the contiguous name block
    # De-duplicate, preserve order.
    seen: dict[str, None] = {}
    for nm in names:
        seen.setdefault(nm, None)
    return list(seen)


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
