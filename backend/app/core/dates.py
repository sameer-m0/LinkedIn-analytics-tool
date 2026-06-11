"""Date range resolution for dashboard filtering and comparison.

This module is pure (no I/O) so it is trivially unit-testable. ``today`` is
always injectable to keep tests deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


class RangePreset(str, Enum):
    LAST_7 = "last_7"
    LAST_30 = "last_30"
    LAST_90 = "last_90"
    MTD = "mtd"
    QTD = "qtd"
    YTD = "ytd"
    ALL_TIME = "all_time"
    CUSTOM = "custom"


class ComparisonMode(str, Enum):
    PREVIOUS_PERIOD = "previous_period"
    SAME_PERIOD_LAST_YEAR = "same_period_last_year"
    NONE = "none"


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date  # inclusive

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("DateRange.start must be <= end")


def _quarter_start(d: date) -> date:
    q_month = ((d.month - 1) // 3) * 3 + 1
    return date(d.year, q_month, 1)


def resolve_range(
    preset: RangePreset,
    *,
    today: date,
    custom_start: date | None = None,
    custom_end: date | None = None,
    all_time_floor: date | None = None,
) -> DateRange:
    """Resolve a preset into a concrete inclusive ``DateRange``.

    ``all_time_floor`` is the earliest date present in the data; used so
    ALL_TIME does not span an unbounded window.
    """
    if preset is RangePreset.CUSTOM:
        if not (custom_start and custom_end):
            raise ValueError("Custom range requires custom_start and custom_end")
        return DateRange(custom_start, custom_end)

    if preset is RangePreset.LAST_7:
        return DateRange(today - timedelta(days=6), today)
    if preset is RangePreset.LAST_30:
        return DateRange(today - timedelta(days=29), today)
    if preset is RangePreset.LAST_90:
        return DateRange(today - timedelta(days=89), today)
    if preset is RangePreset.MTD:
        return DateRange(date(today.year, today.month, 1), today)
    if preset is RangePreset.QTD:
        return DateRange(_quarter_start(today), today)
    if preset is RangePreset.YTD:
        return DateRange(date(today.year, 1, 1), today)
    if preset is RangePreset.ALL_TIME:
        floor = all_time_floor or date(today.year - 5, 1, 1)
        return DateRange(min(floor, today), today)

    raise ValueError(f"Unsupported preset: {preset}")


def comparison_range(current: DateRange, mode: ComparisonMode) -> DateRange | None:
    """Compute the comparison window for delta calculations."""
    if mode is ComparisonMode.NONE:
        return None
    if mode is ComparisonMode.PREVIOUS_PERIOD:
        length = current.days
        prev_end = current.start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=length - 1)
        return DateRange(prev_start, prev_end)
    if mode is ComparisonMode.SAME_PERIOD_LAST_YEAR:
        try:
            return DateRange(
                current.start.replace(year=current.start.year - 1),
                current.end.replace(year=current.end.year - 1),
            )
        except ValueError:  # Feb 29 -> Feb 28
            return DateRange(
                current.start.replace(year=current.start.year - 1, day=28)
                if current.start.month == 2 and current.start.day == 29
                else current.start.replace(year=current.start.year - 1),
                current.end.replace(year=current.end.year - 1, day=28)
                if current.end.month == 2 and current.end.day == 29
                else current.end.replace(year=current.end.year - 1),
            )
    return None


def pct_delta(current: float | None, previous: float | None) -> float | None:
    """Percentage change current vs previous. ``None`` when undefined."""
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / abs(previous) * 100.0
