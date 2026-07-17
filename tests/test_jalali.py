"""Tests for the Jalali date template filter."""

from datetime import datetime

import jdatetime
from django.test import TestCase

from services.templatetags.jalali_tags import jalali, persian_digits, to_persian_digits


class TestJalaliFilterUsesJdatetime(TestCase):
    """Verify our filter produces correct Jalali dates via jdatetime."""

    def test_today(self):
        dt = datetime(2026, 7, 15, 12, 0)
        jd = jdatetime.date.fromgregorian(year=dt.year, month=dt.month, day=dt.day)
        result = jalali(dt, "YYYY/MM/DD")
        expected = f"{to_persian_digits(str(jd.year))}/{to_persian_digits(f'{jd.month:02d}')}/{to_persian_digits(f'{jd.day:02d}')}"
        assert result == expected

    def test_nowruz(self):
        dt = datetime(2026, 3, 20, 12, 0)
        result = jalali(dt, "YYYY/MN/DD")
        assert "۱۴۰۵" in result or "۱۴۰۴" in result

    def test_filter_year_matches_jdatetime(self):
        for dt_args in [
            (2026, 7, 15),
            (2026, 3, 20),
            (2025, 3, 20),
            (2024, 3, 20),
            (2025, 1, 1),
        ]:
            dt = datetime(*dt_args, 12, 0)
            jd = jdatetime.date.fromgregorian(year=dt.year, month=dt.month, day=dt.day)
            result = jalali(dt, "YYYY")
            assert result == to_persian_digits(str(jd.year)), (
                f"For {dt_args}: got {result}, "
                f"expected {to_persian_digits(str(jd.year))}"
            )


class TestToPersianDigits(TestCase):
    """Tests for the to_persian_digits helper."""

    def test_all_digits_converted(self):
        assert to_persian_digits("0123456789") == "۰۱۲۳۴۵۶۷۸۹"

    def test_mixed_string(self):
        assert to_persian_digits("page 3 of 10") == "page ۳ of ۱۰"

    def test_no_digits(self):
        assert to_persian_digits("hello") == "hello"

    def test_empty_string(self):
        assert to_persian_digits("") == ""


class TestPersianDigitsFilter(TestCase):
    """Tests for the fa template filter."""

    def test_integer(self):
        assert persian_digits(42) == "۴۲"

    def test_string(self):
        assert persian_digits("123") == "۱۲۳"

    def test_none_returns_empty(self):
        assert persian_digits(None) == ""

    def test_float(self):
        assert persian_digits(3.5) == "۳.۵"


class TestJalaliFilter(TestCase):
    """Tests for the jalali template filter formatting."""

    def test_default_format(self):
        dt = datetime(2025, 10, 1, 14, 30)
        result = jalali(dt)
        assert "مهر" in result
        assert "۱۴:۳۰" in result
        assert "-" in result

    def test_date_only_format(self):
        dt = datetime(2025, 4, 1, 10, 0)
        result = jalali(dt, "DD MN YYYY")
        assert "فروردین" in result

    def test_time_only(self):
        dt = datetime(2025, 6, 15, 8, 5)
        result = jalali(dt, "HH:mm")
        assert result == "۰۸:۰۵"

    def test_none_returns_empty(self):
        assert jalali(None) == ""

    def test_persian_digits_not_english(self):
        dt = datetime(2026, 7, 15, 0, 0)
        result = jalali(dt, "YYYY")
        for ch in result:
            assert ord(ch) > 127
