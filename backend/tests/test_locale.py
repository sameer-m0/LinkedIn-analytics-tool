from datetime import date

import pytest

from app.parsers.locale import detect_dayfirst, parse_date, parse_number


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1,234", 1234.0),
        ("1.234", 1.234),
        ("1,234.56", 1234.56),
        ("1.234,56", 1234.56),
        ("1 234", 1234.0),
        ("12,5%", 0.125),
        ("5%", 0.05),
        ("-", None),
        ("", None),
        (1000, 1000.0),
    ],
)
def test_parse_number(raw, expected):
    assert parse_number(raw) == expected


def test_parse_date_us_default():
    assert parse_date("03/04/2024") == date(2024, 3, 4)  # MM/DD


def test_parse_date_dayfirst():
    assert parse_date("03/04/2024", dayfirst=True) == date(2024, 4, 3)  # DD/MM


def test_parse_date_iso():
    assert parse_date("2024-03-04") == date(2024, 3, 4)


def test_parse_date_unambiguous_day():
    # 25 cannot be a month -> resolves regardless of dayfirst guess.
    assert parse_date("25/12/2024", dayfirst=True) == date(2024, 12, 25)


def test_detect_dayfirst():
    assert detect_dayfirst(["13/01/2024", "14/01/2024"]) is True
    assert detect_dayfirst(["01/13/2024", "01/14/2024"]) is False
