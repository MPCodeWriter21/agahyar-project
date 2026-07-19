"""Custom validators for Iranian-specific data formats.

Provides ``iranian_phone_number_validator`` for 11-digit mobile
numbers starting with ``09``, and Persian password validators that
replace Django's default English messages.
"""

import re

from django.contrib.auth.password_validation import (
    CommonPasswordValidator as _BaseCommon,
)
from django.contrib.auth.password_validation import (
    MinimumLengthValidator as _BaseMinLength,
)
from django.contrib.auth.password_validation import (
    NumericPasswordValidator as _BaseNumeric,
)
from django.contrib.auth.password_validation import (
    UserAttributeSimilarityValidator as _BaseSimilar,
)
from django.core.exceptions import ValidationError

from .error_codes import get_error_message

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def normalize_phone(value: str) -> str:
    """Translate Persian digits to English and strip whitespace.

    :param value: The phone number string (may contain Persian digits).
    :returns: A string with only ASCII digits and no surrounding whitespace.
    """
    return value.strip().translate(PERSIAN_DIGITS)


def iranian_phone_number_validator(value: str) -> None:
    """Validate that *value* is a valid Iranian mobile number (11 digits starting with 09).

    :param value: The phone number string to validate.
    :raises ValidationError: If the number does not match the expected pattern.
    """
    if not re.match(r"^09\d{9}$", value):
        raise ValidationError(
            "Phone number must be 11 digits and start with 09.",
        )


def center_phone_validator(value: str) -> None:
    """Validate a service-center phone number.

    Accepts 11-digit Iranian numbers (landline or mobile).  Persian
    digits are expected to have been normalised *before* this
    validator runs.

    :param value: The phone number string to validate.
    :raises ValidationError: If the number does not match the expected pattern.
    """
    if not re.match(r"^0\d{10}$", value):
        raise ValidationError(
            "Phone number must be 11 digits starting with 0.",
        )


class PersianMinimumLengthValidator(_BaseMinLength):
    """Same as Django's MinimumLengthValidator but with Persian messages."""

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError as exc:
            raise ValidationError(
                get_error_message("password/too-short"),
                code="password_too_short",
            ) from exc

    def get_help_text(self):
        return get_error_message("password/too-short")


class PersianUserAttributeSimilarityValidator(_BaseSimilar):
    """Same as Django's UserAttributeSimilarityValidator but with Persian messages."""

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError as exc:
            raise ValidationError(
                get_error_message("password/too-similar"),
                code="password_too_similar",
            ) from exc

    def get_help_text(self):
        return get_error_message("password/too-similar")


class PersianCommonPasswordValidator(_BaseCommon):
    """Same as Django's CommonPasswordValidator but with Persian messages."""

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError as exc:
            raise ValidationError(
                get_error_message("password/too-common"),
                code="password_too_common",
            ) from exc

    def get_help_text(self):
        return get_error_message("password/too-common")


class PersianNumericPasswordValidator(_BaseNumeric):
    """Same as Django's NumericPasswordValidator but with Persian messages."""

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError as exc:
            raise ValidationError(
                get_error_message("password/numeric-only"),
                code="password_entirely_numeric",
            ) from exc

    def get_help_text(self):
        return get_error_message("password/numeric-only")
