"""Custom validators for Iranian-specific data formats.

Provides ``iranian_phone_number_validator`` for 11-digit mobile
numbers starting with ``09``.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def iranian_phone_number_validator(value: str) -> None:
    """Validate that *value* is a valid Iranian mobile number (11 digits starting with 09).

    :param value: The phone number string to validate.
    :raises ValidationError: If the number does not match the expected pattern.
    """
    if not re.match(r"^09\d{9}$", value):
        raise ValidationError(
            _("Phone number must be 11 digits and start with 09."),
        )
