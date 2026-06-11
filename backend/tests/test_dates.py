from datetime import date

from app.core.dates import (
    ComparisonMode,
    DateRange,
    RangePreset,
    comparison_range,
    pct_delta,
    resolve_range,
)

TODAY = date(2024, 3, 15)


def test_last_7():
    r = resolve_range(RangePreset.LAST_7, today=TODAY)
    assert r == DateRange(date(2024, 3, 9), date(2024, 3, 15))
    assert r.days == 7


def test_mtd():
    r = resolve_range(RangePreset.MTD, today=TODAY)
    assert r.start == date(2024, 3, 1) and r.end == TODAY


def test_qtd():
    r = resolve_range(RangePreset.QTD, today=TODAY)
    assert r.start == date(2024, 1, 1)


def test_ytd():
    r = resolve_range(RangePreset.YTD, today=TODAY)
    assert r.start == date(2024, 1, 1)


def test_previous_period():
    cur = DateRange(date(2024, 3, 9), date(2024, 3, 15))
    prev = comparison_range(cur, ComparisonMode.PREVIOUS_PERIOD)
    assert prev == DateRange(date(2024, 3, 2), date(2024, 3, 8))


def test_same_period_last_year():
    cur = DateRange(date(2024, 3, 9), date(2024, 3, 15))
    prev = comparison_range(cur, ComparisonMode.SAME_PERIOD_LAST_YEAR)
    assert prev == DateRange(date(2023, 3, 9), date(2023, 3, 15))


def test_pct_delta():
    assert pct_delta(110, 100) == 10.0
    assert pct_delta(50, 100) == -50.0
    assert pct_delta(5, 0) is None
    assert pct_delta(None, 100) is None
