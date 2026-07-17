"""Tests for the Agahyar REST API endpoints.

Covers happy paths, edge cases, validation errors, authentication
boundaries, and ensures no 500 errors from user input.
"""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from services.models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    PhoneVerification,
    Service,
    ServiceCenter,
)


class ServiceAPITest(TestCase):
    """Tests for the /api/v1/services/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.service = Service.objects.create(
            name="شناسنامه",
            organization="ثبت احوال",
            documents="کارت ملی|عکس",
            steps="مراجعه به دفتر|تکمیل فرم",
            cost="رایگان",
            duration="۳ روز",
            keywords="شناسنامه هویت",
        )
        self.url = "/api/v1/services/"

    def test_list_services(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_retrieve_service(self):
        resp = self.client.get(f"{self.url}{self.service.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "شناسنامه")
        self.assertIn("documents_list", resp.data)
        self.assertIn("steps_list", resp.data)

    def test_documents_list_split(self):
        resp = self.client.get(f"{self.url}{self.service.id}/")
        self.assertEqual(resp.data["documents_list"], ["کارت ملی", "عکس"])

    def test_steps_list_split(self):
        resp = self.client.get(f"{self.url}{self.service.id}/")
        self.assertEqual(resp.data["steps_list"], ["مراجعه به دفتر", "تکمیل فرم"])

    def test_search_by_name(self):
        resp = self.client.get(f"{self.url}?search=شناسنامه")
        self.assertEqual(resp.data["count"], 1)

    def test_search_no_results(self):
        resp = self.client.get(f"{self.url}?search=غیروجودی")
        self.assertEqual(resp.data["count"], 0)

    def test_filter_by_organization(self):
        resp = self.client.get(f"{self.url}?organization=ثبت احوال")
        self.assertEqual(resp.data["count"], 1)

    def test_centers_count_annotation(self):
        ServiceCenter.objects.create(
            service=self.service,
            name="دفتر مرکزی",
            address="تهران",
            city="تهران",
        )
        ServiceCenter.objects.create(
            service=self.service,
            name="دفتر جنوب",
            address="تهران",
            city="تهران",
        )
        resp = self.client.get(f"{self.url}{self.service.id}/")
        self.assertEqual(resp.data["centers_count"], 2)

    def test_centers_count_zero(self):
        resp = self.client.get(f"{self.url}{self.service.id}/")
        self.assertEqual(resp.data["centers_count"], 0)

    def test_read_only_no_create(self):
        resp = self.client.post(self.url, {"name": "test"})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_read_only_no_update(self):
        resp = self.client.put(f"{self.url}{self.service.id}/", {"name": "test"})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_read_only_no_delete(self):
        resp = self.client.delete(f"{self.url}{self.service.id}/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrieve_nonexistent_returns_404(self):
        resp = self.client.get(f"{self.url}99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_page_returns_valid_response(self):
        resp = self.client.get(f"{self.url}?page=abc")
        self.assertIn(
            resp.status_code,
            [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_200_OK,
            ],
        )


class ProfileAPIAdditionalTests(TestCase):
    """Additional edge-case and security tests for profile endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/profile/"
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="علی",
            last_name="احمدی",
            email="ali@example.com",
        )
        from services.models import UserProfile

        self.profile = UserProfile.objects.create(
            user=self.user,
            city="تهران",
            neighborhood="ونک",
            phone="09123456789",
        )

    def test_patch_requires_auth(self):
        resp = self.client.patch(self.url, {"first_name": "محمد"}, format="json")
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_put_returns_405(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(self.url, {"first_name": "محمد"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_returns_405(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_response_body_contains_updated_values(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            self.url, {"first_name": "محمد", "city": "اصفهان"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["first_name"], "محمد")
        self.assertEqual(resp.data["city"], "اصفهان")
        self.assertEqual(resp.data["last_name"], "احمدی")
        self.assertEqual(resp.data["username"], "testuser")

    def test_get_response_does_not_leak_sensitive_fields(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", resp.data)
        self.assertNotIn("is_staff", resp.data)
        self.assertNotIn("is_superuser", resp.data)
        self.assertNotIn("id", resp.data)

    def test_patch_first_name_too_long_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"first_name": "a" * 31}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_last_name_too_long_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"last_name": "a" * 31}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_city_too_long_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"city": "a" * 101}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_empty_first_name_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"first_name": ""}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_empty_last_name_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"last_name": ""}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_empty_city_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"city": ""}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_username_field_ignored(self):
        """Username should not be changeable through profile PATCH."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"username": "hacked"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "testuser")

    def test_patch_phone_field_ignored(self):
        """Phone should not be changeable through profile PATCH."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"phone": "09987654321"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "09123456789")

    def test_profile_after_logout_returns_401(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.client.post("/api/v1/auth/logout/")
        self.client.force_authenticate(user=None)
        self.client.credentials()
        resp = self.client.get(self.url)
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


class ChangePhoneAdditionalTests(TestCase):
    """Additional edge-case and security tests for phone change endpoints."""

    FIXED_OTP = "123456"

    def setUp(self):
        self.client = APIClient()
        self.request_url = "/api/v1/auth/profile/change-phone/"
        self.verify_url = "/api/v1/auth/profile/verify-phone/"
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        from services.models import UserProfile

        self.profile = UserProfile.objects.create(
            user=self.user,
            city="تهران",
            phone="09123456789",
        )

    def test_non_numeric_otp_rejected(self):
        self.client.force_authenticate(user=self.user)
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value="123456"),
        ):
            resp = self.client.post(
                self.request_url, {"new_phone": "09987654321"}, format="json"
            )
        token = resp.data["pending_token"]
        resp = self.client.post(
            self.verify_url,
            {"pending_token": token, "otp_code": "abcdef"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_otp_reuse_after_phone_change_rejected(self):
        self.client.force_authenticate(user=self.user)
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value=self.FIXED_OTP),
        ):
            resp = self.client.post(
                self.request_url, {"new_phone": "09987654321"}, format="json"
            )
        token = resp.data["pending_token"]
        resp = self.client.post(
            self.verify_url,
            {"pending_token": token, "otp_code": self.FIXED_OTP},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Try to reuse the same OTP
        resp = self.client.post(
            self.verify_url,
            {"pending_token": token, "otp_code": self.FIXED_OTP},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_phone_put_returns_405(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(
            self.request_url, {"new_phone": "09987654321"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_verify_phone_put_returns_405(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(self.verify_url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_verify_phone_get_returns_405(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.verify_url)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_concurrent_phone_change_requests(self):
        """Second phone change request should be handled gracefully."""
        self.client.force_authenticate(user=self.user)
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value="111111"),
        ):
            resp1 = self.client.post(
                self.request_url, {"new_phone": "09987654321"}, format="json"
            )
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value="222222"),
        ):
            resp2 = self.client.post(
                self.request_url, {"new_phone": "09987654322"}, format="json"
            )
        # Both should succeed (independent requests)
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        # Verify the first one's token still works
        resp = self.client.post(
            self.verify_url,
            {"pending_token": resp1.data["pending_token"], "otp_code": "111111"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "09987654321")


class OTPCodeValidationTest(TestCase):
    """Tests for OTP code validation (must be exactly 6 digits)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        from services.models import UserProfile

        UserProfile.objects.create(
            user=self.user,
            city="تهران",
            phone="09123456789",
        )

    def test_verify_otp_with_letters_rejected(self):
        resp = self.client.post(
            "/api/v1/auth/verify-otp/",
            {"pending_token": "fake", "otp_code": "abcdef"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_with_special_chars_rejected(self):
        resp = self.client.post(
            "/api/v1/auth/verify-otp/",
            {"pending_token": "fake", "otp_code": "!@#$%^"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_with_too_few_digits_rejected(self):
        resp = self.client.post(
            "/api/v1/auth/verify-otp/",
            {"pending_token": "fake", "otp_code": "12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_with_too_many_digits_rejected(self):
        resp = self.client.post(
            "/api/v1/auth/verify-otp/",
            {"pending_token": "fake", "otp_code": "1234567"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_with_mixed_accepted(self):
        """DRF CharField trims whitespace, so ' 123456 ' -> '123456' which is valid."""
        resp = self.client.post(
            "/api/v1/auth/verify-otp/",
            {"pending_token": "fake", "otp_code": " 123456 "},
            format="json",
        )
        # Should pass serializer validation (whitespace trimmed), then fail on pending_token
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST])
        # Verify it's not failing on the OTP format (would be a different error)
        self.assertNotIn("otp_code", resp.data)

    def test_verify_otp_with_decimal_rejected(self):
        resp = self.client.post(
            "/api/v1/auth/verify-otp/",
            {"pending_token": "fake", "otp_code": "1234.56"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class MaskPhoneTest(TestCase):
    """Tests for _mask_phone utility function."""

    def test_normal_phone(self):
        from services.auth_api import _mask_phone

        self.assertEqual(_mask_phone("09123456789"), "0912***6789")

    def test_seven_digit_phone(self):
        from services.auth_api import _mask_phone

        self.assertEqual(_mask_phone("0912345"), "0912***2345")

    def test_six_digit_phone(self):
        from services.auth_api import _mask_phone

        self.assertEqual(_mask_phone("091234"), "09***34")

    def test_five_digit_phone(self):
        from services.auth_api import _mask_phone

        self.assertEqual(_mask_phone("09123"), "09***23")

    def test_four_digit_phone(self):
        from services.auth_api import _mask_phone

        self.assertEqual(_mask_phone("0912"), "09***12")

    def test_three_digit_phone(self):
        from services.auth_api import _mask_phone

        self.assertEqual(_mask_phone("091"), "***")

    def test_empty_phone(self):
        from services.auth_api import _mask_phone

        self.assertEqual(_mask_phone(""), "***")


class CommentFilterValidationTest(TestCase):
    """Tests for comment query parameter validation."""

    def test_both_service_and_center_rejected(self):
        from services.models import Service

        service = Service.objects.create(
            name="خدمت", organization="سازمان", documents="م", steps="م"
        )
        resp = self.client.get(
            f"/api/v1/comments/?service={service.id}&service_center=1"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_integer_service_rejected(self):
        resp = self.client.get("/api/v1/comments/?service=abc")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_integer_center_rejected(self):
        resp = self.client.get("/api/v1/comments/?service_center=xyz")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_service_param_works(self):
        from services.models import Service

        service = Service.objects.create(
            name="خدمت", organization="سازمان", documents="م", steps="م"
        )
        resp = self.client.get(f"/api/v1/comments/?service={service.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_valid_center_param_works(self):
        from services.models import Service, ServiceCenter

        service = Service.objects.create(
            name="خدمت", organization="سازمان", documents="م", steps="م"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز", address="آدرس", city="تهران"
        )
        resp = self.client.get(f"/api/v1/comments/?service_center={center.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ProfileAPITest(TestCase):
    """Tests for GET/PATCH /api/v1/auth/profile/."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/profile/"
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="علی",
            last_name="احمدی",
            email="ali@example.com",
        )
        from services.models import UserProfile

        self.profile = UserProfile.objects.create(
            user=self.user,
            city="تهران",
            neighborhood="ونک",
            phone="09123456789",
        )

    def test_get_requires_auth(self):
        resp = self.client.get(self.url)
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_get_returns_profile(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "testuser")
        self.assertEqual(resp.data["first_name"], "علی")
        self.assertEqual(resp.data["last_name"], "احمدی")
        self.assertEqual(resp.data["email"], "ali@example.com")
        self.assertEqual(resp.data["city"], "تهران")
        self.assertEqual(resp.data["neighborhood"], "ونک")
        self.assertEqual(resp.data["phone"], "09123456789")

    def test_patch_updates_first_name(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"first_name": "محمد"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "محمد")

    def test_patch_updates_last_name(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"last_name": "رضایی"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, "رضایی")

    def test_patch_updates_city(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"city": "اصفهان"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.city, "اصفهان")

    def test_patch_updates_neighborhood(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"neighborhood": "جلفا"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.neighborhood, "جلفا")

    def test_patch_updates_email(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"email": "new@example.com"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")

    def test_patch_clears_email(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"email": ""}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "")

    def test_patch_multiple_fields(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            self.url,
            {"first_name": "محمد", "city": "شیراز", "neighborhood": "زرگری"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "محمد")
        self.assertEqual(self.profile.city, "شیراز")
        self.assertEqual(self.profile.neighborhood, "زرگری")

    def test_patch_does_not_change_phone(self):
        """Phone is read-only in profile PATCH; use /change-phone/ instead."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"phone": "09987654321"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "09123456789")

    def test_patch_duplicate_email_rejected(self):
        User.objects.create_user(
            username="other", password="pass123", email="taken@example.com"
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            self.url, {"email": "taken@example.com"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_same_email_accepted(self):
        """Keeping your own email should not be rejected as duplicate."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"email": "ali@example.com"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_patch_invalid_email_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {"email": "not-an-email"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_empty_body_accepted(self):
        """An empty PATCH should be a no-op, not an error."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_patch_never_500(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(self.url, "not json", content_type="text/plain")
        self.assertLess(resp.status_code, 500)

    def test_get_never_500(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertLess(resp.status_code, 500)


class ChangePhoneAPITest(TestCase):
    """Tests for POST /api/v1/auth/profile/change-phone/ + verify-phone/."""

    FIXED_OTP = "123456"

    def setUp(self):
        self.client = APIClient()
        self.request_url = "/api/v1/auth/profile/change-phone/"
        self.verify_url = "/api/v1/auth/profile/verify-phone/"
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        from services.models import UserProfile

        self.profile = UserProfile.objects.create(
            user=self.user,
            city="تهران",
            phone="09123456789",
        )

    def _request_phone_change(self, new_phone="09987654321"):
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value=self.FIXED_OTP),
        ):
            return self.client.post(
                self.request_url,
                {"new_phone": new_phone},
                format="json",
            )

    def _verify_phone_change(self, pending_token, code=None):
        return self.client.post(
            self.verify_url,
            {"pending_token": pending_token, "otp_code": code or self.FIXED_OTP},
            format="json",
        )

    def _full_phone_change(self, new_phone="09987654321"):
        req_resp = self._request_phone_change(new_phone)
        token = req_resp.data["pending_token"]
        verify_resp = self._verify_phone_change(token)
        return req_resp, verify_resp

    # --- Step 1: request phone change ---

    def test_request_requires_auth(self):
        resp = self.client.post(
            self.request_url, {"new_phone": "09987654321"}, format="json"
        )
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_request_returns_pending_token(self, _mock_otp):
        self.client.force_authenticate(user=self.user)
        resp = self._request_phone_change()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("pending_token", resp.data)
        self.assertIn("new_phone", resp.data)
        self.assertIn("***", resp.data["new_phone"])

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_request_masks_new_phone(self, _mock_otp):
        self.client.force_authenticate(user=self.user)
        resp = self._request_phone_change("09987654321")
        self.assertEqual(resp.data["new_phone"], "0998***4321")

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_request_same_phone_rejected(self, _mock_otp):
        self.client.force_authenticate(user=self.user)
        resp = self._request_phone_change("09123456789")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_request_duplicate_phone_rejected(self, _mock_otp):
        other = User.objects.create_user(username="other", password="pass123")
        from services.models import UserProfile

        UserProfile.objects.create(user=other, phone="09987654321", city="تهران")
        self.client.force_authenticate(user=self.user)
        resp = self._request_phone_change("09987654321")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_invalid_phone_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.request_url, {"new_phone": "123"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_missing_phone_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.request_url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(DISABLE_SMS=True)
    def test_request_sms_failure_returns_502(self):
        from services.sms import SMSAPIError

        self.client.force_authenticate(user=self.user)
        with patch("services.auth_api.get_sms_client") as mock_get:
            mock_client = mock_get.return_value
            mock_client.send_otp.side_effect = SMSAPIError("fail")
            resp = self._request_phone_change()
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "09123456789")

    def test_request_never_500(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.request_url, "not json", content_type="text/plain")
        self.assertLess(resp.status_code, 500)

    # --- Step 2: verify OTP + update phone ---

    def test_verify_creates_new_phone(self):
        self.client.force_authenticate(user=self.user)
        _, verify_resp = self._full_phone_change()
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "09987654321")

    def test_verify_returns_updated_profile(self):
        self.client.force_authenticate(user=self.user)
        _, verify_resp = self._full_phone_change()
        self.assertEqual(verify_resp.data["phone"], "09987654321")
        self.assertEqual(verify_resp.data["username"], "testuser")

    def test_verify_wrong_code_rejected(self):
        self.client.force_authenticate(user=self.user)
        req_resp = self._request_phone_change()
        token = req_resp.data["pending_token"]
        resp = self._verify_phone_change(token, code="999999")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "09123456789")

    def test_verify_invalid_token_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self._verify_phone_change("garbage-token")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_empty_body_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.verify_url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_requires_auth(self):
        resp = self.client.post(
            self.verify_url,
            {"pending_token": "x", "otp_code": "123456"},
            format="json",
        )
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_verify_otp_marked_as_used(self):
        self.client.force_authenticate(user=self.user)
        self._full_phone_change()
        verification = PhoneVerification.objects.filter(phone="09987654321").first()
        self.assertIsNotNone(verification)
        self.assertTrue(verification.is_used)

    def test_verify_expired_pending_token(self):
        from services.auth_api import _delete_phone_change_token

        self.client.force_authenticate(user=self.user)
        req_resp = self._request_phone_change()
        token = req_resp.data["pending_token"]
        _delete_phone_change_token(token)
        resp = self._verify_phone_change(token)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_expired_otp_code(self):
        from datetime import timedelta

        from django.utils import timezone

        self.client.force_authenticate(user=self.user)
        req_resp = self._request_phone_change()
        token = req_resp.data["pending_token"]

        verification = PhoneVerification.objects.filter(phone="09987654321").first()
        verification.created_at = timezone.now() - timedelta(minutes=10)
        verification.save(update_fields=["created_at"])

        resp = self._verify_phone_change(token)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "09123456789")

    def test_verify_different_user_token_rejected(self):
        """A token from a different user's phone change must be rejected."""
        other = User.objects.create_user(username="other", password="pass123")
        from services.models import UserProfile

        UserProfile.objects.create(user=other, city="تهران", phone="09111111111")

        # Other user requests phone change
        other_client = APIClient()
        other_client.force_authenticate(user=other)
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value=self.FIXED_OTP),
        ):
            other_resp = other_client.post(
                self.request_url,
                {"new_phone": "09222222222"},
                format="json",
            )
        token = other_resp.data["pending_token"]

        # Our user tries to use it
        self.client.force_authenticate(user=self.user)
        resp = self._verify_phone_change(token)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "09123456789")

    def test_verify_never_500(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.verify_url, "not json", content_type="text/plain")
        self.assertLess(resp.status_code, 500)

    # --- Full flow: register -> change phone ---

    def test_register_then_change_phone(self):
        """Full lifecycle: register, then change phone via OTP."""
        client = APIClient()

        # Register with a unique phone (different from setUp's profile)
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value="123456"),
        ):
            reg_resp = client.post(
                "/api/v1/auth/register/",
                {
                    "username": "flowuser",
                    "password": "securepass123",
                    "first_name": "علی",
                    "last_name": "محمدی",
                    "city": "تهران",
                    "neighborhood": "ونک",
                    "phone": "09300000001",
                },
                format="json",
            )
        token = reg_resp.data["pending_token"]
        resp = client.post(
            "/api/v1/auth/verify-otp/",
            {"pending_token": token, "otp_code": "123456"},
            format="json",
        )
        auth_token = resp.data["token"]
        client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token}")

        # Change phone
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value="654321"),
        ):
            phone_resp = client.post(
                "/api/v1/auth/profile/change-phone/",
                {"new_phone": "09987654321"},
                format="json",
            )
        self.assertEqual(phone_resp.status_code, status.HTTP_200_OK)
        pt = phone_resp.data["pending_token"]

        resp = client.post(
            "/api/v1/auth/profile/verify-phone/",
            {"pending_token": pt, "otp_code": "654321"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["phone"], "09987654321")


class ServiceCenterAPITest(TestCase):
    """Tests for the /api/v1/centers/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.service = Service.objects.create(
            name="گواهینامه",
            organization="پلیس راهور",
            documents="کارت ملی",
            steps="آزمون",
        )
        self.center = ServiceCenter.objects.create(
            service=self.service,
            name="مرکز تست",
            address="خیابان ولیعصر",
            city="تهران",
            phone="02112345678",
        )
        self.url = "/api/v1/centers/"

    def test_list_centers(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_retrieve_center(self):
        resp = self.client.get(f"{self.url}{self.center.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["service_name"], "گواهینامه")

    def test_filter_by_city(self):
        resp = self.client.get(f"{self.url}?city=تهران")
        self.assertEqual(resp.data["count"], 1)

    def test_filter_by_city_no_match(self):
        resp = self.client.get(f"{self.url}?city=اصفهان")
        self.assertEqual(resp.data["count"], 0)

    def test_filter_by_service(self):
        resp = self.client.get(f"{self.url}?service={self.service.id}")
        self.assertEqual(resp.data["count"], 1)

    def test_filter_by_nonexistent_service(self):
        resp = self.client.get(f"{self.url}?service=99999")
        self.assertEqual(resp.data["count"], 0)

    def test_search_center(self):
        resp = self.client.get(f"{self.url}?search=ولیعصر")
        self.assertEqual(resp.data["count"], 1)

    def test_read_only(self):
        resp = self.client.post(self.url, {"name": "test"})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrieve_nonexistent_returns_404(self):
        resp = self.client.get(f"{self.url}99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_avg_rating_none_when_no_ratings(self):
        resp = self.client.get(f"{self.url}{self.center.id}/")
        self.assertIsNone(resp.data["avg_rating"])

    def test_avg_rating_computed(self):
        u1 = User.objects.create_user(username="u1", password="pass123")
        u2 = User.objects.create_user(username="u2", password="pass123")
        CenterRating.objects.create(user=u1, service_center=self.center, score=4)
        CenterRating.objects.create(user=u2, service_center=self.center, score=2)
        resp = self.client.get(f"{self.url}{self.center.id}/")
        self.assertAlmostEqual(resp.data["avg_rating"], 3.0)


class FAQAPITest(TestCase):
    """Tests for the /api/v1/faqs/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.faq = FAQ.objects.create(
            question="چگونه ثبت نام کنم؟",
            answer="از بخش ثبت نام اقدام کنید.",
            category="ثبت نام",
            order=1,
        )
        self.url = "/api/v1/faqs/"

    def test_list_faqs(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertEqual(len(resp.data), 1)

    def test_retrieve_faq(self):
        resp = self.client.get(f"{self.url}{self.faq.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["question"], "چگونه ثبت نام کنم؟")

    def test_search_faq(self):
        resp = self.client.get(f"{self.url}?search=ثبت نام")
        self.assertIsInstance(resp.data, list)
        self.assertEqual(len(resp.data), 1)

    def test_search_faq_no_match(self):
        resp = self.client.get(f"{self.url}?search=موضوع ناموجود")
        self.assertIsInstance(resp.data, list)
        self.assertEqual(len(resp.data), 0)

    def test_read_only(self):
        resp = self.client.post(self.url, {"question": "test"})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_retrieve_nonexistent_returns_404(self):
        resp = self.client.get(f"{self.url}99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class CommentAPITest(TestCase):
    """Tests for the /api/v1/comments/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.service = Service.objects.create(
            name="خدمت آزمایشی", organization="سازمان آزمایش", documents="م", steps="م"
        )
        self.center = ServiceCenter.objects.create(
            service=self.service, name="مرکز تست", address="آدرس", city="تهران"
        )
        self.comment = Comment.objects.create(
            user=self.user, service=self.service, text="نظر تستی"
        )
        self.url = "/api/v1/comments/"

    def test_list_public(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_retrieve(self):
        resp = self.client.get(f"{self.url}{self.comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["text"], "نظر تستی")

    def test_filter_by_service(self):
        resp = self.client.get(f"{self.url}?service={self.service.id}")
        self.assertEqual(resp.data["count"], 1)

    def test_filter_by_center(self):
        Comment.objects.create(user=self.user, service_center=self.center, text="مرکزی")
        resp = self.client.get(f"{self.url}?service_center={self.center.id}")
        self.assertEqual(resp.data["count"], 1)

    def test_replies_nested(self):
        Comment.objects.create(
            user=self.user, service=self.service, text="پاسخ", parent=self.comment
        )
        resp = self.client.get(f"{self.url}{self.comment.id}/")
        self.assertEqual(len(resp.data["replies"]), 1)
        self.assertEqual(resp.data["replies"][0]["text"], "پاسخ")

    def test_reply_to_reply_not_in_list(self):
        """Deeply nested replies must not appear as top-level comments."""
        reply = Comment.objects.create(
            user=self.user, service=self.service, text="پاسخ", parent=self.comment
        )
        deep = Comment.objects.create(
            user=self.user, service=self.service, text="عمیق", parent=reply
        )
        resp = self.client.get(self.url)
        ids = [c["id"] for c in resp.data["results"]]
        self.assertNotIn(deep.id, ids)
        self.assertNotIn(reply.id, ids)
        self.assertIn(self.comment.id, ids)

    # --- Authentication ---

    def test_create_requires_auth(self):
        resp = self.client.post(self.url, {"service": self.service.id, "text": "hi"})
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_create_authenticated(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service": self.service.id, "text": "نظر جدید"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)

    def test_delete_requires_auth(self):
        resp = self.client.delete(f"{self.url}{self.comment.id}/")
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    # --- Ownership: edit/delete only own comments ---

    def test_update_own_comment(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"{self.url}{self.comment.id}/",
            {"text": "ویرایش شده"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, "ویرایش شده")

    def test_update_other_users_comment_denied(self):
        other = User.objects.create_user(username="other", password="pass123")
        other_comment = Comment.objects.create(
            user=other, service=self.service, text="دیگری"
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"{self.url}{other_comment.id}/",
            {"text": "تغییر غیرمجاز"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        other_comment.refresh_from_db()
        self.assertEqual(other_comment.text, "دیگری")

    def test_cannot_change_target_on_update(self):
        """Comment target (service/service_center) must be immutable."""
        other_service = Service.objects.create(
            name="دیگر", organization="سازمان دیگر", documents="م", steps="م"
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"{self.url}{self.comment.id}/",
            {"service": other_service.id, "text": "تغییر هدف"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.service_id, self.service.id)

    def test_cannot_change_parent_on_update(self):
        """Comment parent must be immutable."""
        other_comment = Comment.objects.create(
            user=self.user, service=self.service, text="دیگری"
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"{self.url}{self.comment.id}/",
            {"parent": other_comment.id, "text": "تغییر والد"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertIsNone(self.comment.parent_id)

    def test_delete_own_comment(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"{self.url}{self.comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)
        self.assertEqual(self.comment.deleted_by, self.user)

    def test_delete_other_users_comment_denied(self):
        other = User.objects.create_user(username="other", password="pass123")
        other_comment = Comment.objects.create(
            user=other, service=self.service, text="دیگری"
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"{self.url}{other_comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        other_comment.refresh_from_db()
        self.assertFalse(other_comment.is_deleted)

    # --- Validation: targets ---

    def test_no_target_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {"text": "بدون هدف"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_both_targets_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url,
            {
                "service": self.service.id,
                "service_center": self.center.id,
                "text": "هر دو",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_service_id_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service": 99999, "text": "ناموجود"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_center_id_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_center": 99999, "text": "ناموجود"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Validation: parent ---

    def test_parent_from_different_target_rejected(self):
        self.client.force_authenticate(user=self.user)
        other_service = Service.objects.create(
            name="دیگر", organization="سازمان دیگر", documents="م", steps="م"
        )
        other_comment = Comment.objects.create(
            user=self.user, service=other_service, text="دیگری"
        )
        resp = self.client.post(
            self.url,
            {
                "service": self.service.id,
                "parent": other_comment.id,
                "text": "وابسته",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reply_to_reply_rejected(self):
        self.client.force_authenticate(user=self.user)
        reply = Comment.objects.create(
            user=self.user, service=self.service, text="پاسخ", parent=self.comment
        )
        resp = self.client.post(
            self.url,
            {
                "service": self.service.id,
                "parent": reply.id,
                "text": "عمیق",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_reply_accepted(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url,
            {
                "service": self.service.id,
                "parent": self.comment.id,
                "text": "پاسخ معتبر",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    # --- Validation: text ---

    def test_empty_text_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service": self.service.id, "text": "   "}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_long_text_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url,
            {"service": self.service.id, "text": "x" * 2001},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exact_max_length_text_accepted(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url,
            {"service": self.service.id, "text": "x" * 2000},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    # --- Nonexistent comment ---

    def test_retrieve_nonexistent_returns_404(self):
        resp = self.client.get(f"{self.url}99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class CenterRatingAPITest(TestCase):
    """Tests for the /api/v1/ratings/ endpoint.

    Ratings are private. Users can only see and manage their own.
    Average rating is exposed via the center detail endpoint.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other = User.objects.create_user(username="other", password="pass123")
        self.service = Service.objects.create(
            name="خدمت", organization="سازمان", documents="م", steps="م"
        )
        self.center = ServiceCenter.objects.create(
            service=self.service, name="مرکز", address="آدرس", city="تهران"
        )
        self.url = "/api/v1/ratings/"

    # --- Public access blocked ---

    def test_list_get_not_allowed(self):
        """GET /ratings/ must not be allowed (only POST is registered)."""
        CenterRating.objects.create(user=self.user, service_center=self.center, score=5)
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_list_unauthenticated_returns_401_or_405(self):
        resp = self.client.get(self.url)
        self.assertIn(
            resp.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_405_METHOD_NOT_ALLOWED,
            ],
        )

    def test_retrieve_get_not_allowed(self):
        """GET /ratings/<id>/ must not be allowed (only DELETE is registered)."""
        r = CenterRating.objects.create(
            user=self.user, service_center=self.center, score=5
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"{self.url}{r.id}/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # --- GET /mine/ ---

    def test_mine_requires_auth(self):
        resp = self.client.get(f"{self.url}mine/?service_center={self.center.id}")
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_mine_returns_own_rating(self):
        CenterRating.objects.create(user=self.user, service_center=self.center, score=4)
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"{self.url}mine/?service_center={self.center.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["score"], 4)
        self.assertEqual(resp.data["service_center"], self.center.id)

    def test_mine_returns_404_when_no_rating(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"{self.url}mine/?service_center={self.center.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_mine_does_not_show_other_users_rating(self):
        """mine/ must only return the caller's rating, not others."""
        CenterRating.objects.create(
            user=self.other, service_center=self.center, score=2
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"{self.url}mine/?service_center={self.center.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_mine_requires_center_param(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"{self.url}mine/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Create / Update ---

    def test_create_requires_auth(self):
        resp = self.client.post(
            self.url, {"service_center": self.center.id, "score": 4}, format="json"
        )
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_create_authenticated(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_center": self.center.id, "score": 4}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["score"], 4)
        self.assertNotIn("user", resp.data)

    def test_duplicate_rating_updates(self):
        CenterRating.objects.create(user=self.user, service_center=self.center, score=3)
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_center": self.center.id, "score": 5}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["score"], 5)

    # --- Delete ---

    def test_delete_own_rating(self):
        r = CenterRating.objects.create(
            user=self.user, service_center=self.center, score=3
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"{self.url}{r.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CenterRating.objects.filter(id=r.id).exists())

    def test_delete_other_users_rating_denied(self):
        """Users must not be able to delete another user's rating."""
        r = CenterRating.objects.create(
            user=self.other, service_center=self.center, score=3
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"{self.url}{r.id}/")
        # View returns 404 (not 403) to avoid leaking existence of
        # other users' ratings.
        self.assertIn(
            resp.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
            ],
        )

    # --- Validation: score ---

    def test_score_too_low_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_center": self.center.id, "score": 0}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_score_too_high_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_center": self.center.id, "score": 6}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_score_not_integer_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_center": self.center.id, "score": "abc"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_score_boundaries(self):
        self.client.force_authenticate(user=self.user)
        for s in [1, 5]:
            existing = CenterRating.objects.filter(
                user=self.user, service_center=self.center
            ).first()
            if existing:
                existing.delete()
            resp = self.client.post(
                self.url, {"service_center": self.center.id, "score": s}, format="json"
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    # --- Validation: service_center ---

    def test_missing_center_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {"score": 4}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_center_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_center": 99999, "score": 4}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- No user data leak ---

    def test_response_never_contains_user_field(self):
        """Rating responses must never expose user information."""
        CenterRating.objects.create(user=self.user, service_center=self.center, score=5)
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"{self.url}mine/?service_center={self.center.id}")
        self.assertNotIn("user", resp.data)

    def test_create_response_no_user_field(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_center": self.center.id, "score": 4}, format="json"
        )
        self.assertNotIn("user", resp.data)


class CommentEditDeleteAPITest(TestCase):
    """Tests for comment soft-delete, edit, and admin delete via API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("apiuser", password="pass12345")
        self.token = Token.objects.create(user=self.user)
        self.service = Service.objects.create(
            name="svc", organization="org", documents="d", steps="s"
        )
        self.comment = Comment.objects.create(
            user=self.user, service=self.service, text="original"
        )

    def test_delete_sets_deleted_by(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        resp = self.client.delete(f"/api/v1/comments/{self.comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)
        self.assertEqual(self.comment.deleted_by, self.user)

    def test_delete_other_users_comment_denied(self):
        other = User.objects.create_user("other", password="pass12345")
        other_token = Token.objects.create(user=other)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token}")
        resp = self.client.delete(f"/api/v1/comments/{self.comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_deleted)

    def test_staff_can_delete_any_comment(self):
        admin = User.objects.create_user("admin", password="pass12345", is_staff=True)
        admin_token = Token.objects.create(user=admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {admin_token}")
        resp = self.client.delete(f"/api/v1/comments/{self.comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)
        self.assertEqual(self.comment.deleted_by, admin)

    def test_edit_sets_edited_at(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        resp = self.client.patch(
            f"/api/v1/comments/{self.comment.id}/",
            {"text": "updated"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, "updated")
        self.assertIsNotNone(self.comment.edited_at)

    def test_edit_after_24h_denied(self):
        from datetime import timedelta

        self.comment.created_at = timezone.now() - timedelta(hours=25)
        self.comment.save(update_fields=["created_at"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        resp = self.client.patch(
            f"/api/v1/comments/{self.comment.id}/",
            {"text": "expired"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, "original")

    def test_edit_deleted_comment_denied(self):
        self.comment.deleted_by = self.user
        self.comment.save(update_fields=["deleted_by"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        resp = self.client.patch(
            f"/api/v1/comments/{self.comment.id}/",
            {"text": "deleted"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reply_to_deleted_comment_denied(self):
        self.comment.deleted_by = self.user
        self.comment.save(update_fields=["deleted_by"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        resp = self.client.post(
            "/api/v1/comments/",
            {
                "service": self.service.id,
                "text": "reply",
                "parent": self.comment.id,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deleted_comment_shows_is_deleted_in_list(self):
        self.comment.deleted_by = self.user
        self.comment.save(update_fields=["deleted_by"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        resp = self.client.get(f"/api/v1/comments/?service={self.service.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data["results"]
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["is_deleted"])


class BookmarkAPITest(TestCase):
    """Tests for the /api/v1/bookmarks/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.service = Service.objects.create(
            name="خدمت", organization="سازمان", documents="م", steps="م"
        )
        self.url = "/api/v1/bookmarks/"

    def test_requires_auth(self):
        resp = self.client.get(self.url)
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_list_empty(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_create(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_id": self.service.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bookmark.objects.count(), 1)

    def test_duplicate_returns_error(self):
        Bookmark.objects.create(user=self.user, service=self.service)
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_id": self.service.id}, format="json"
        )
        self.assertIn(
            resp.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT],
        )

    def test_duplicate_never_500(self):
        """The IntegrityError must never propagate to the client."""
        Bookmark.objects.create(user=self.user, service=self.service)
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.url, {"service_id": self.service.id}, format="json"
        )
        self.assertLess(resp.status_code, 500)

    def test_delete(self):
        bm = Bookmark.objects.create(user=self.user, service=self.service)
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"{self.url}{bm.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_delete_nonexistent_returns_404(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.delete(f"{self.url}99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_isolation(self):
        """Users can only see their own bookmarks."""
        other = User.objects.create_user(username="other", password="pass123")
        Bookmark.objects.create(user=other, service=self.service)

        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.data["count"], 0)

    def test_invalid_service_id_rejected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {"service_id": 99999}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_not_allowed(self):
        """Bookmarks cannot be updated -- only created or deleted."""
        bm = Bookmark.objects.create(user=self.user, service=self.service)
        self.client.force_authenticate(user=self.user)
        resp = self.client.put(
            f"{self.url}{bm.id}/", {"service_id": self.service.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update_not_allowed(self):
        bm = Bookmark.objects.create(user=self.user, service=self.service)
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"{self.url}{bm.id}/", {"service_id": self.service.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SchemaViewTest(TestCase):
    """Tests for the API schema and docs endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_api_schema(self):
        resp = self.client.get("/api/v1/schema/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_docs(self):
        resp = self.client.get("/api/v1/docs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_docs_self_hosted_assets(self):
        """Swagger UI must reference self-hosted static files, not CDN."""
        resp = self.client.get("/api/v1/docs/")
        content = resp.content.decode()
        self.assertIn("libs/swagger-ui/swagger-ui-bundle.js", content)
        self.assertIn("libs/swagger-ui/swagger-ui.css", content)
        self.assertNotIn("cdn.jsdelivr.net", content)

    def test_api_root(self):
        resp = self.client.get("/api/v1/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("services", resp.data)

    def test_nonexistent_api_path(self):
        resp = self.client.get("/api/v1/nonexistent/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class No500OnBadInputTest(TestCase):
    """Ensure no endpoint returns 500 for well-formed but invalid requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="p123")

    def test_garbage_json_to_comments(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/v1/comments/",
            "not json",
            content_type="text/plain",
        )
        self.assertLess(resp.status_code, 500)

    def test_empty_body_to_bookmarks(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/v1/bookmarks/", {}, format="json")
        self.assertLess(resp.status_code, 500)

    def test_empty_body_to_ratings(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/v1/ratings/", {}, format="json")
        self.assertLess(resp.status_code, 500)

    def test_ratings_list_returns_405_not_500(self):
        """GET /ratings/ is not registered -- must return 405, never 500."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/v1/ratings/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_nonexistent_pk_to_retrieve(self):
        for path in [
            "/api/v1/services/99999/",
            "/api/v1/centers/99999/",
            "/api/v1/faqs/99999/",
            "/api/v1/comments/99999/",
        ]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class RegisterAPITest(TestCase):
    """Tests for the 2-step /api/v1/auth/register/ + /api/v1/auth/verify-otp/ flow."""

    FIXED_OTP = "123456"

    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/v1/auth/register/"
        self.verify_url = "/api/v1/auth/verify-otp/"
        self.valid_data = {
            "username": "newuser",
            "password": "securepass123",
            "first_name": "علی",
            "last_name": "احمدی",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09123456789",
        }

    def _send_otp(self, data=None):
        """Step 1: send OTP and return response."""
        return self.client.post(
            self.register_url, data or self.valid_data, format="json"
        )

    def _verify_otp(self, pending_token, code=None):
        """Step 2: verify OTP and return response."""
        return self.client.post(
            self.verify_url,
            {"pending_token": pending_token, "otp_code": code or self.FIXED_OTP},
            format="json",
        )

    def _full_register(self, data=None):
        """Complete 2-step registration and return (register_resp, verify_resp)."""
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value=self.FIXED_OTP),
        ):
            reg_resp = self._send_otp(data)
        token = reg_resp.data["pending_token"]
        verify_resp = self._verify_otp(token)
        return reg_resp, verify_resp

    # --- Step 1: register (send OTP) ---

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_register_step1_returns_pending_token(self, _mock_otp):
        resp = self._send_otp()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("pending_token", resp.data)
        self.assertIn("phone", resp.data)
        self.assertIn("***", resp.data["phone"])

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_register_step1_masks_phone(self, _mock_otp):
        resp = self._send_otp()
        self.assertEqual(resp.data["phone"], "0912***6789")

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_register_step1_no_user_created(self, _mock_otp):
        self._send_otp()
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_step1_missing_fields_rejected(self):
        resp = self.client.post(self.register_url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_step1_missing_phone_rejected(self):
        data = {k: v for k, v in self.valid_data.items() if k != "phone"}
        resp = self._send_otp(data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_step1_missing_neighborhood_rejected(self):
        data = {k: v for k, v in self.valid_data.items() if k != "neighborhood"}
        resp = self._send_otp(data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_step1_duplicate_username_rejected(self):
        User.objects.create_user(username="newuser", password="pass123")
        resp = self._send_otp()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_step1_duplicate_phone_rejected(self):
        from services.models import UserProfile

        u = User.objects.create_user(username="other", password="pass123")
        UserProfile.objects.create(user=u, phone="09123456789", city="تهران")
        resp = self._send_otp()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_step1_short_password_rejected(self):
        data = {**self.valid_data, "password": "short"}
        resp = self._send_otp(data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_register_step1_invalid_phone_rejected(self, _mock_otp):
        data = {**self.valid_data, "phone": "123"}
        resp = self._send_otp(data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(DISABLE_SMS=True)
    def test_register_step1_sms_failure_returns_502(self):
        from services.sms import SMSAPIError

        with patch("services.auth_api.get_sms_client") as mock_get:
            mock_client = mock_get.return_value
            mock_client.send_otp.side_effect = SMSAPIError("fail")
            resp = self._send_otp()
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)

    def test_register_step1_never_500(self):
        resp = self.client.post(
            self.register_url, "not json", content_type="text/plain"
        )
        self.assertLess(resp.status_code, 500)

    # --- Step 2: verify OTP + create account ---

    def test_verify_otp_creates_user(self):
        reg_resp, verify_resp = self._full_register()
        self.assertEqual(verify_resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_verify_otp_returns_token(self):
        _, verify_resp = self._full_register()
        self.assertIn("token", verify_resp.data)
        self.assertTrue(Token.objects.filter(key=verify_resp.data["token"]).exists())

    def test_verify_otp_creates_profile(self):
        _, verify_resp = self._full_register()
        user = User.objects.get(username="newuser")
        self.assertEqual(user.profile.city, "تهران")
        self.assertEqual(user.profile.neighborhood, "ونک")
        self.assertEqual(user.profile.phone, "09123456789")

    def test_verify_otp_sets_names(self):
        _, verify_resp = self._full_register()
        user = User.objects.get(username="newuser")
        self.assertEqual(user.first_name, "علی")
        self.assertEqual(user.last_name, "احمدی")

    def test_verify_otp_wrong_code_rejected(self):
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value=self.FIXED_OTP),
        ):
            reg_resp = self._send_otp()
        token = reg_resp.data["pending_token"]
        resp = self._verify_otp(token, code="999999")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_verify_otp_invalid_token_rejected(self):
        resp = self._verify_otp("garbage-token", code=self.FIXED_OTP)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_empty_body_rejected(self):
        resp = self.client.post(self.verify_url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_code_marked_as_used(self):
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value=self.FIXED_OTP),
        ):
            reg_resp = self._send_otp()
        token = reg_resp.data["pending_token"]
        self._verify_otp(token)
        verification = PhoneVerification.objects.filter(phone="09123456789").first()
        self.assertIsNotNone(verification)
        self.assertTrue(verification.is_used)

    def test_verify_otp_reuse_same_token_fails(self):
        """After successful verification, the same pending_token should fail."""
        reg_resp, _ = self._full_register()
        token = reg_resp.data["pending_token"]
        resp = self._verify_otp(token)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_expired_pending_token(self):
        """A pending_token that has been deleted from cache should fail."""
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value=self.FIXED_OTP),
        ):
            reg_resp = self._send_otp()
        token = reg_resp.data["pending_token"]
        # Manually delete from cache to simulate expiry
        from services.auth_api import _delete_pending_token

        _delete_pending_token(token)
        resp = self._verify_otp(token)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_expired_code(self):
        """An OTP that has passed OTP_EXPIRE_MINUTES should be rejected."""
        from datetime import timedelta

        from django.utils import timezone

        with (
            override_settings(DISABLE_SMS=True),
            patch("services.auth_api.generate_otp", return_value=self.FIXED_OTP),
        ):
            reg_resp = self._send_otp()
        token = reg_resp.data["pending_token"]

        # Backdate the verification to simulate expiry
        verification = PhoneVerification.objects.filter(phone="09123456789").first()
        verification.created_at = timezone.now() - timedelta(minutes=10)
        verification.save(update_fields=["created_at"])

        resp = self._verify_otp(token)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_verify_never_500(self):
        resp = self.client.post(self.verify_url, "not json", content_type="text/plain")
        self.assertLess(resp.status_code, 500)


class LoginAPITest(TestCase):
    """Tests for the /api/v1/auth/login/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/login/"
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_login_success(self):
        resp = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("token", resp.data)
        self.assertEqual(resp.data["username"], "testuser")

    def test_login_returns_existing_token(self):
        existing_token = Token.objects.create(user=self.user)
        resp = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(resp.data["token"], existing_token.key)

    def test_login_wrong_password(self):
        resp = self.client.post(
            self.url,
            {"username": "testuser", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        resp = self.client.post(
            self.url,
            {"username": "nobody", "password": "pass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_empty_body(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_never_500(self):
        resp = self.client.post(self.url, "not json", content_type="text/plain")
        self.assertLess(resp.status_code, 500)


class LogoutAPITest(TestCase):
    """Tests for the /api/v1/auth/logout/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/logout/"
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)

    def test_logout_success(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_logout_requires_auth(self):
        resp = self.client.post(self.url)
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_logout_with_token_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())

    def test_logout_twice_is_idempotent(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class AuthIntegrationTest(TestCase):
    """End-to-end test: register (2-step with OTP) -> use token -> logout."""

    FIXED_OTP = "123456"

    @override_settings(DISABLE_SMS=True)
    @patch("services.auth_api.generate_otp", return_value="123456")
    def test_full_flow(self, _mock_otp):
        client = APIClient()

        # Step 1: register (send OTP)
        resp = client.post(
            "/api/v1/auth/register/",
            {
                "username": "flowuser",
                "password": "securepass123",
                "first_name": "علی",
                "last_name": "محمدی",
                "city": "تهران",
                "neighborhood": "ونک",
                "phone": "09123456789",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        pending_token = resp.data["pending_token"]

        # Step 2: verify OTP
        resp = client.post(
            "/api/v1/auth/verify-otp/",
            {"pending_token": pending_token, "otp_code": self.FIXED_OTP},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        token = resp.data["token"]

        # Use token to create a comment
        client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        service = Service.objects.create(
            name="خدمت", organization="سازمان", documents="م", steps="م"
        )
        resp = client.post(
            "/api/v1/comments/",
            {"service": service.id, "text": "نظر از اپ"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Logout
        resp = client.post("/api/v1/auth/logout/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Token no longer works
        resp = client.post(
            "/api/v1/comments/",
            {"service": service.id, "text": "باید رد شود"},
            format="json",
        )
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
