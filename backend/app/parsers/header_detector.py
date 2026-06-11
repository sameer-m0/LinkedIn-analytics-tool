"""Heuristic header-row detection.

LinkedIn exports frequently prepend title/metadata rows, so the real header is
not row 0. We score each candidate row by how many cells look like *labels*
(non-empty, mostly text, not pure numbers/dates) and how well the row below it
looks like *data*. The best-scoring row wins.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from app.parsers.synonyms import resolve_header

_NUMERIC = re.compile(r"^[\s\d.,%\-]+$")


@dataclass
class HeaderDetection:
    header_row: int
    headers: list[str]
    known_count: int  # how many headers matched a known synonym


def _looks_like_label(cell: object) -> bool:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return False
    s = str(cell).strip()
    if not s:
        return False
    return not _NUMERIC.match(s)  # labels contain letters


def _score_row(row: list[object]) -> tuple[int, int]:
    non_empty = [c for c in row if c is not None and str(c).strip() and not pd.isna(c)]
    label_like = sum(1 for c in non_empty if _looks_like_label(c))
    known = sum(
        1 for c in non_empty if resolve_header(str(c)) is not None
    )
    return label_like, known


def detect_header(df: pd.DataFrame, *, max_scan: int = 15) -> HeaderDetection:
    """Find the header row in a raw (header=None) DataFrame."""
    best: tuple[int, int, int] = (-1, 0, 0)  # (row, label_like, known)
    scan = min(max_scan, len(df))
    for i in range(scan):
        row = list(df.iloc[i].values)
        label_like, known = _score_row(row)
        if label_like < 2:
            continue
        # Prefer rows that match known synonyms; break ties by label richness.
        candidate = (i, label_like, known)
        if (known, label_like) > (best[2], best[1]):
            best = candidate

    header_row = best[0] if best[0] >= 0 else 0
    headers = [
        str(c).strip() if c is not None and not pd.isna(c) else f"col_{j}"
        for j, c in enumerate(df.iloc[header_row].values)
    ]
    known_count = sum(1 for h in headers if resolve_header(h) is not None)
    return HeaderDetection(header_row=header_row, headers=headers, known_count=known_count)
