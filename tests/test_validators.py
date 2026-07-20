"""Tests for custom validators in the services application.

Focuses on Iranian phone number validation at both the
standalone validator level and the ``UserProfile`` model field.
"""

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from services.models import UserProfile
from services.validators import (
    center_phone_validator,
    iranian_phone_number_validator,
    normalize_phone,
)


class TestIranianPhoneNumberValidator:
    def test_valid_phone_numbers(self):
        iranian_phone_number_validator("09121234567")
        iranian_phone_number_validator("09991234567")
        iranian_phone_number_validator("09011234567")

    def test_invalid_phone_number_too_short(self):
        with pytest.raises(ValidationError):
            iranian_phone_number_validator("0912123456")

    def test_invalid_phone_number_too_long(self):
        with pytest.raises(ValidationError):
            iranian_phone_number_validator("091212345678")

    def test_invalid_phone_number_wrong_prefix(self):
        with pytest.raises(ValidationError):
            iranian_phone_number_validator("02121234567")

    def test_invalid_phone_number_non_digit(self):
        with pytest.raises(ValidationError):
            iranian_phone_number_validator("0912abc4567")


@pytest.mark.django_db
class TestUserProfilePhoneValidation:
    def test_valid_phone_saves_successfully(self):
        user = User.objects.create_user("testuser", password="pass12345")
        profile = UserProfile.objects.create(
            user=user, city="Tehran", phone="09121234567"
        )
        assert profile.phone == "09121234567"

    def test_blank_phone_is_allowed(self):
        user = User.objects.create_user("testuser2", password="pass12345")
        profile = UserProfile.objects.create(user=user, city="Tehran")
        assert profile.phone == ""

    def test_invalid_phone_raises_error(self):
        user = User.objects.create_user("testuser3", password="pass12345")
        with pytest.raises(ValidationError):
            profile = UserProfile(user=user, city="Tehran", phone="12345")
            profile.full_clean()


class TestNormalizePhone:
    def test_converts_persian_digits(self):
        assert normalize_phone("۰۲۱۱۲۳۴۵۶۷") == "0211234567"

    def test_converts_mixed_digits(self):
        assert normalize_phone("۰۹۱۲abc۴۵۶۷") == "0912abc4567"

    def test_already_english(self):
        assert normalize_phone("02112345678") == "02112345678"

    def test_strips_whitespace(self):
        assert normalize_phone("  02112345678  ") == "02112345678"

    def test_empty_string(self):
        assert normalize_phone("") == ""


class TestCenterPhoneValidator:
    def test_valid_landline(self):
        center_phone_validator("02112345678")

    def test_valid_mobile(self):
        center_phone_validator("09121234567")

    def test_invalid_too_short(self):
        with pytest.raises(ValidationError):
            center_phone_validator("0211234567")

    def test_invalid_too_long(self):
        with pytest.raises(ValidationError):
            center_phone_validator("021123456789")

    def test_invalid_prefix(self):
        with pytest.raises(ValidationError):
            center_phone_validator("12112345678")


@pytest.mark.django_db
class TestServiceCenterPhoneClean:
    def test_persian_digits_normalised_on_clean(self):
        from services.models import Service, ServiceCenter, ServiceCenterPhone

        service = Service.objects.create(
            name="خدمت", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(name="مرکز", address="آدرس", city="تهران")
        center.services.add(service)
        phone = ServiceCenterPhone(center=center, phone="۰۲۱۱۲۳۴۵۶۷۸")
        phone.full_clean()
        assert phone.phone == "02112345678"
