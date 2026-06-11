"""Locale-aware normalization of numbers and dates.

LinkedIn exports vary by the account's locale. We must accept:
  numbers : "1,234"  "1.234"  "1 234"  "12,5%"  "1,234.56"  "1.234,56"
  dates   : MM/DD/YYYY, DD/MM/YYYY, ISO, Excel serial, datetime objects.

The functions here are pure and individually unit-tested.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta

_THOUSANDS = re.compile(r"[  ]")  # spaces / non-breaking spaces as group sep


def parse_number(raw: object) -> float | None:
    """Parse a possibly-localized numeric string into a float.

    Heuristic for the ambiguous ``,``/``.`` case: whichever separator appears
    *last* is treated as the decimal separator.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return None if (isinstance(raw, float) and math.isnan(raw)) else float(raw)

    s = str(raw).strip()
    if not s or s.lower() in {"nan", "n/a", "-", "—", "null"}:
        return None

    is_pct = s.endswith("%")
    s = s.rstrip("%").strip()
    s = _THOUSANDS.sub("", s)

    has_comma, has_dot = "," in s, "." in s
    if has_comma and has_dot:
        # Last-seen separator is the decimal mark.
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif has_comma:
        # Single comma: decimal if it looks like "12,5"; else thousands.
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    # only dots or plain digits -> leave as-is

    try:
        val = float(s)
    except ValueError:
        return None
    return val / 100.0 if is_pct else val


# Excel's epoch (with the well-known 1900 leap-year bug offset handled by openpyxl
# at read time, but raw serials from some files need this fallback).
_EXCEL_EPOCH = date(1899, 12, 30)


def parse_date(raw: object, *, dayfirst: bool = False) -> date | None:
    """Parse a date value. ``dayfirst`` disambiguates MM/DD vs DD/MM."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if isinstance(raw, (int, float)) and not (isinstance(raw, float) and math.isnan(raw)):
        # Treat as Excel serial day number.
        return _EXCEL_EPOCH + timedelta(days=int(raw))

    s = str(raw).strip()
    if not s:
        return None

    # ISO first — unambiguous.
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    m = re.match(r"(\d{1,4})[/\-.](\d{1,2})[/\-.](\d{1,4})", s)
    if m:
        a, b, c = (int(x) for x in m.groups())
        if a > 31:  # YYYY-first
            return _safe_date(a, b, c)
        year = c if c > 99 else 2000 + c
        if dayfirst:
            return _safe_date(year, b, a)
        return _safe_date(year, a, b)

    # Fallback to dateutil for textual months ("Jan 5, 2024").
    try:
        from dateutil import parser as duparser

        return duparser.parse(s, dayfirst=dayfirst).date()
    except (ValueError, OverflowError, ImportError):
        return None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        # Probably day/month swapped relative to our guess; try the other order.
        try:
            return date(year, day, month)
        except ValueError:
            return None


def detect_dayfirst(samples: list[str]) -> bool:
    """Infer day-first ordering from a column of date strings.

    If any sample has a first component > 12, it must be a day -> day-first.
    Defaults to False (US MM/DD/YYYY), matching LinkedIn's default export.
    """
    for s in samples:
        m = re.match(r"(\d{1,4})[/\-.](\d{1,2})", str(s).strip())
        if m:
            first, second = int(m.group(1)), int(m.group(2))
            if first > 31:  # year-first, irrelevant
                continue
            if first > 12 and second <= 12:
                return True
            if second > 12 and first <= 12:
                return False
    return False
