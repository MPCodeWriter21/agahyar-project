"""Template tags and filters for Jalali (Persian) date formatting."""

import jdatetime
from django import template
from django.utils import timezone

register = template.Library()

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

PERSIAN_MONTHS = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}


def to_persian_digits(value: str) -> str:
    """Convert English digits in a string to Persian digits."""
    return value.translate(PERSIAN_DIGITS)


@register.filter(name="jalali")
def jalali(value, fmt="DD MN YYYY - HH:mm"):
    """Format a datetime as Jalali date with Persian month names and digits.

    Supported format tokens:

    - ``YYYY`` -- Jalali 4-digit year
    - ``MM``   -- Jalali month (01-12)
    - ``DD``   -- Jalali day (01-31)
    - ``HH``   -- hour (00-23)
    - ``mm``   -- minute (00-59)
    - ``MN``   -- Persian month name

    All numeric values are rendered in Persian digits.

    Example usage::

        {{ comment.created_at|jalali }}
        {{ user.date_joined|jalali:"DD MN YYYY" }}
    """
    if value is None:
        return ""

    if timezone.is_aware(value):
        value = timezone.localtime(value)

    jd = jdatetime.date.fromgregorian(year=value.year, month=value.month, day=value.day)
    jt = jdatetime.time(hour=value.hour, minute=value.minute)

    month_name = PERSIAN_MONTHS.get(jd.month, "")

    result = fmt
    result = result.replace("YYYY", to_persian_digits(str(jd.year)))
    result = result.replace("MM", to_persian_digits(f"{jd.month:02d}"))
    result = result.replace("DD", to_persian_digits(f"{jd.day:02d}"))
    result = result.replace("MN", month_name)
    result = result.replace("HH", to_persian_digits(f"{jt.hour:02d}"))
    result = result.replace("mm", to_persian_digits(f"{jt.minute:02d}"))
    return result


@register.filter(name="fa")
def persian_digits(value):
    """Convert any number or string to Persian digits.

    Example usage::

        {{ 42|fa }}
        {{ comment.id|fa }}
    """
    if value is None:
        return ""
    return to_persian_digits(str(value))
