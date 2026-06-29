import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from services.models import UserProfile
from services.validators import iranian_phone_number_validator


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
