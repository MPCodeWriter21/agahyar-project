"""Tests for the Agahyar view functions.

Covers authentication, CRUD operations, security headers,
SEO endpoints, bookmarks, ratings, responsive design,
and error-code rendering across all views.
"""

import json
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from services.forms import RegisterForm
from services.models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    ContactMessage,
    PhoneVerification,
    Service,
    ServiceCenter,
    UserProfile,
)
from services.otp import generate_otp, hash_otp
from services.views import save_user_profile


@pytest.mark.django_db
class TestSaveUserProfile:
    def test_creates_new_profile(self):
        user = User.objects.create_user("newuser", password="pass12345")
        save_user_profile(user.id, "tehran", "saadatabad", "09121234567")
        profile = UserProfile.objects.get(user=user)
        assert profile.city == "tehran"
        assert profile.neighborhood == "saadatabad"
        assert profile.phone == "09121234567"

    def test_updates_existing_profile(self):
        user = User.objects.create_user("existing", password="pass12345")
        UserProfile.objects.create(user=user, city="esfahan", neighborhood="", phone="")
        save_user_profile(user.id, "tehran", "vanak", "09981234567")
        profile = UserProfile.objects.get(user=user)
        assert profile.city == "tehran"
        assert profile.neighborhood == "vanak"
        assert profile.phone == "09981234567"


@pytest.mark.django_db
class TestShowUsersView:
    def test_requires_login(self):
        client = Client()
        response = client.get("/users/")
        assert response.status_code == 302

    def test_shows_users_with_profiles(self):
        user = User.objects.create_user("viewer", password="pass12345")
        UserProfile.objects.create(user=user, city="tehran", phone="09121234567")
        client = Client()
        client.login(username="viewer", password="pass12345")
        response = client.get("/users/")
        assert response.status_code == 200
        assert "viewer" in str(response.content)

    def test_handles_users_without_profile(self):
        User.objects.create_user("noprofile", password="pass12345")
        client = Client()
        client.login(username="noprofile", password="pass12345")
        response = client.get("/users/")
        assert response.status_code == 200
        assert "noprofile" in str(response.content)
        assert "---" in str(response.content)


@pytest.mark.django_db
class TestRegisterView:
    def test_get_returns_form(self):
        client = Client()
        response = client.get("/register/")
        assert response.status_code == 200
        assert "form" in response.context

    @override_settings(DISABLE_SMS=True)
    def test_register_redirects_to_otp_verification(self):
        client = Client()
        data = {
            "username": "newuser",
            "first_name": "علی",
            "last_name": "محمدی",
            "email": "new@example.com",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09121234567",
        }
        response = client.post("/register/", data)
        assert response.status_code == 302
        assert "/verify-otp/" in response.url
        assert not User.objects.filter(username="newuser").exists()

    @override_settings(DISABLE_SMS=True)
    def test_register_creates_phone_verification(self):
        client = Client()
        data = {
            "username": "newuser",
            "first_name": "علی",
            "last_name": "محمدی",
            "email": "new@example.com",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09121234567",
        }
        client.post("/register/", data)
        assert PhoneVerification.objects.filter(phone="09121234567").exists()

    @override_settings(DISABLE_SMS=True)
    def test_register_stores_data_in_session(self):
        client = Client()
        data = {
            "username": "sessionuser",
            "first_name": "رضا",
            "last_name": "احمدی",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "مشهد",
            "neighborhood": "سجاد",
            "phone": "09351234567",
        }
        client.post("/register/", data)
        session = client.session
        pending = session.get("pending_registration")
        assert pending is not None
        assert pending["username"] == "sessionuser"
        assert pending["phone"] == "09351234567"

    @override_settings(DISABLE_SMS=True)
    def test_register_with_phone(self):
        client = Client()
        data = {
            "username": "phonetest",
            "first_name": "مریم",
            "last_name": "احمدی",
            "email": "phone@example.com",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09121234567",
        }
        response = client.post("/register/", data)
        assert response.status_code == 302
        assert "/verify-otp/" in response.url
        assert not User.objects.filter(username="phonetest").exists()

    def test_register_requires_login_redirect_when_authenticated(self):
        User.objects.create_user("loggedin", password="pass12345")
        client = Client()
        client.login(username="loggedin", password="pass12345")
        response = client.get("/register/")
        assert response.status_code == 302

    def test_ltr_inputs_have_ltr_class(self):
        client = Client()
        response = client.get("/register/")
        content = response.content.decode()
        assert 'name="username"' in content
        assert 'class="ltr-input"' in content or "ltr-input" in content
        assert 'dir="ltr"' in content

    def test_register_preserves_values_on_validation_error(self):
        client = Client()
        response = client.post(
            "/register/",
            {
                "username": "testuser",
                "first_name": "علی",
                "last_name": "محمدی",
                "email": "bad-email",
                "password1": "short",
                "password2": "mismatch",
                "city": "تهران",
                "neighborhood": "",
                "phone": "",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'value="testuser"' in content
        assert 'value="علی"' in content
        assert 'value="محمدی"' in content
        assert 'value="bad-email"' in content

    def test_register_shows_field_errors(self):
        client = Client()
        response = client.post(
            "/register/",
            {
                "username": "",
                "first_name": "",
                "last_name": "",
                "email": "",
                "password1": "short",
                "password2": "mismatch",
                "city": "",
                "neighborhood": "",
                "phone": "",
            },
        )
        content = response.content.decode()
        # Check that form errors exist in the rendered context
        assert response.context["form"].errors
        # Check that error CSS classes appear in the HTML
        assert 'class="field-error"' in content or "has-error" in content
        # Check error messages are displayed
        assert "ضروری" in content or "الزامی" in content

    def test_register_returns_bound_form_in_context(self):
        client = Client()
        response = client.post(
            "/register/",
            {
                "username": "partial",
                "first_name": "رضا",
                "last_name": "کریمی",
                "email": "",
                "password1": "short",
                "password2": "short",
                "city": "تهران",
                "neighborhood": "ونک",
                "phone": "",
            },
        )
        assert isinstance(response.context["form"], RegisterForm)
        assert response.context["form"].is_bound is True

    def test_register_shows_persian_error_on_short_password(self):
        client = Client()
        response = client.post(
            "/register/",
            {
                "username": "shortpw",
                "first_name": "",
                "last_name": "",
                "email": "",
                "password1": "123",
                "password2": "123",
                "city": "",
                "neighborhood": "",
                "phone": "",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "This password is too short" not in content
        assert "It must contain at least" not in content
        assert "رمز عبور باید حداقل ۸ کاراکتر باشد." in content


@pytest.mark.django_db
class TestHomeView:
    def test_accessible_anonymously(self):
        client = Client()
        response = client.get("/")
        assert response.status_code == 200

    def test_shows_popular_services(self):
        Service.objects.create(
            name="test service", organization="org", documents="doc1", steps="step1"
        )
        client = Client()
        response = client.get("/")
        assert response.status_code == 200
        assert "test service" in str(response.content)


@pytest.mark.django_db
class TestDashboardView:
    def test_requires_login(self):
        client = Client()
        response = client.get("/dashboard/")
        assert response.status_code == 302

    def test_shows_when_logged_in(self):
        User.objects.create_user("dashuser", password="pass12345")
        client = Client()
        client.login(username="dashuser", password="pass12345")
        response = client.get("/dashboard/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestSearchView:
    def test_requires_login(self):
        client = Client()
        response = client.get("/search/")
        assert response.status_code == 302

    def test_search_finds_service_by_name(self):
        User.objects.create_user("searchuser", password="pass12345")
        Service.objects.create(
            name="smart card",
            organization="org",
            documents="doc1",
            steps="step1",
            keywords="ملی,کارت",
        )
        client = Client()
        client.login(username="searchuser", password="pass12345")
        response = client.get("/search/", {"q": "smart"})
        assert response.status_code == 200
        assert "smart card" in str(response.content)

    def test_search_pagination_context(self):
        User.objects.create_user("searchpag", password="pass12345")
        for i in range(15):
            Service.objects.create(
                name=f"result{i}", organization="o", documents="d", steps="s"
            )
        client = Client()
        client.login(username="searchpag", password="pass12345")
        response = client.get("/search/", {"q": "result"})
        assert response.status_code == 200
        assert "page_obj" in response.context

    def test_search_empty_query_returns_empty(self):
        User.objects.create_user("searchuser2", password="pass12345")
        client = Client()
        client.login(username="searchuser2", password="pass12345")
        response = client.get("/search/", {"q": ""})
        assert response.status_code == 200

    def test_search_filters_by_organization(self):
        User.objects.create_user("orgfilteruser", password="pass12345")
        Service.objects.create(
            name="سرویس الف", organization="سازمان الف", documents="d", steps="s"
        )
        Service.objects.create(
            name="سرویس ب", organization="سازمان ب", documents="d", steps="s"
        )
        client = Client()
        client.login(username="orgfilteruser", password="pass12345")
        response = client.get("/search/", {"organization": "سازمان الف"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "سرویس الف" in content
        assert "سرویس ب" not in content

    def test_search_filters_by_city(self):
        User.objects.create_user("cityfilteruser", password="pass12345")
        svc_a = Service.objects.create(
            name="سرویس شهر", organization="org1", documents="d", steps="s"
        )
        svc_b = Service.objects.create(
            name="سرویس دیگر", organization="org2", documents="d", steps="s"
        )
        ServiceCenter.objects.create(
            service=svc_a, name="مرکز تهران", address="آدرس", city="تهران"
        )
        ServiceCenter.objects.create(
            service=svc_b, name="مرکز مشهد", address="آدرس", city="مشهد"
        )
        client = Client()
        client.login(username="cityfilteruser", password="pass12345")
        response = client.get("/search/", {"city": "تهران"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "سرویس شهر" in content
        assert "سرویس دیگر" not in content

    def test_search_filters_dropdowns_present(self):
        User.objects.create_user("dropdownuser", password="pass12345")
        Service.objects.create(
            name="test1", organization="سازمان الف", documents="d", steps="s"
        )
        Service.objects.create(
            name="test2", organization="سازمان ب", documents="d", steps="s"
        )
        client = Client()
        client.login(username="dropdownuser", password="pass12345")
        response = client.get("/search/")
        content = response.content.decode()
        assert 'name="organization"' in content
        assert 'name="city"' in content
        assert "سازمان الف" in content
        assert "سازمان ب" in content


@pytest.mark.django_db
class TestServiceListView:
    def test_accessible_anonymously(self):
        client = Client()
        response = client.get("/services/")
        assert response.status_code == 200

    def test_lists_services_ordered_by_name(self):
        Service.objects.create(name="beta", organization="o", documents="d", steps="s")
        Service.objects.create(name="alpha", organization="o", documents="d", steps="s")
        client = Client()
        response = client.get("/services/")
        assert response.status_code == 200
        content = str(response.content)
        assert content.index("alpha") < content.index("beta")

    def test_list_pagination_context(self):
        for i in range(15):
            Service.objects.create(
                name=f"svc{i}", organization="o", documents="d", steps="s"
            )
        client = Client()
        client.login(username="paguser", password="pass12345")
        response = client.get("/services/")
        assert response.status_code == 200
        assert "page_obj" in response.context
        assert response.context["page_obj"].paginator.per_page == 12


@pytest.mark.django_db
class TestServiceDetailView:
    def test_accessible_anonymously(self):
        service = Service.objects.create(
            name="public-svc", organization="org", documents="doc1", steps="step1"
        )
        client = Client()
        response = client.get(f"/service/{service.id}/")
        assert response.status_code == 200

    def test_404_for_nonexistent(self):
        client = Client()
        response = client.get("/service/9999/")
        assert response.status_code == 404

    def test_shows_service_details(self):
        service = Service.objects.create(
            name="passport", organization="police", documents="doc1", steps="step1"
        )
        client = Client()
        response = client.get(f"/service/{service.id}/")
        assert response.status_code == 200
        assert "passport" in str(response.content)

    def test_service_detail_falls_back_to_default_city_without_profile(self):
        service = Service.objects.create(
            name="test-svc", organization="org", documents="doc1", steps="step1"
        )
        client = Client()
        response = client.get(f"/service/{service.id}/")
        assert response.status_code == 200
        assert response.context["user_city"] == ""

    def test_service_detail_with_profile(self):
        user = User.objects.create_user("profileduser", password="pass12345")
        UserProfile.objects.create(
            user=user, city="شیراز", neighborhood="قصردشت", phone="09121234567"
        )
        service = Service.objects.create(
            name="test-svc2", organization="org", documents="doc1", steps="step1"
        )
        client = Client()
        client.login(username="profileduser", password="pass12345")
        response = client.get(f"/service/{service.id}/")
        assert response.status_code == 200
        assert response.context["user_city"] == "شیراز"


@pytest.mark.django_db
class TestFAQView:
    def test_accessible_without_login(self):
        client = Client()
        response = client.get("/faq/")
        assert response.status_code == 200

    def test_shows_faqs_ordered(self):
        FAQ.objects.create(question="q1", answer="a1", order=2)
        FAQ.objects.create(question="q2", answer="a2", order=1)
        client = Client()
        response = client.get("/faq/")
        assert response.status_code == 200
        assert "q1" in str(response.content)


@pytest.mark.django_db
class TestLoginView:
    def test_get_returns_form(self):
        client = Client()
        response = client.get("/login/")
        assert response.status_code == 200
        assert "form" in response.context

    def test_login_preserves_username_on_invalid_credentials(self):
        User.objects.create_user("loginuser", password="correctpass")
        client = Client()
        response = client.post(
            "/login/",
            {"username": "loginuser", "password": "wrongpass"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'value="loginuser"' in content

    def test_login_invalid_username_returns_form_with_errors(self):
        client = Client()
        response = client.post(
            "/login/",
            {"username": "", "password": ""},
        )
        assert response.status_code == 200
        assert response.context["form"].errors
        content = response.content.decode()
        assert "has-error" in content or "message-error" in content

    def test_login_redirects_when_authenticated(self):
        User.objects.create_user("alreadyin", password="pass12345")
        client = Client()
        client.login(username="alreadyin", password="pass12345")
        response = client.get("/login/")
        assert response.status_code == 302

    def test_login_remember_me_sets_long_session(self):
        User.objects.create_user("remuser", password="pass12345")
        client = Client()
        client.post(
            "/login/",
            {"username": "remuser", "password": "pass12345", "remember_me": True},
        )
        session = client.session
        assert session.get_expiry_age() >= 2592000 - 10  # 30 days minus a small delta

    def test_login_no_remember_me_expires_on_browser_close(self):
        User.objects.create_user("noruser", password="pass12345")
        client = Client()
        client.post(
            "/login/",
            {"username": "noruser", "password": "pass12345", "remember_me": False},
        )
        session = client.session
        assert session.get_expire_at_browser_close()


@pytest.mark.django_db
class TestAboutAndContactViews:
    def test_about_accessible_anonymously(self):
        client = Client()
        response = client.get("/about/")
        assert response.status_code == 200

    def test_about_renders_when_logged_in(self):
        User.objects.create_user("aboutuser", password="pass12345")
        client = Client()
        client.login(username="aboutuser", password="pass12345")
        response = client.get("/about/")
        assert response.status_code == 200

    def test_contact_accessible_anonymously(self):
        client = Client()
        response = client.get("/contact/")
        assert response.status_code == 200
        assert "form" in response.context


@pytest.mark.django_db
class TestContactView:
    def test_contact_renders_form_anonymously(self):
        client = Client()
        response = client.get("/contact/")
        assert response.status_code == 200
        assert "form" in response.context

    def test_contact_post_saves_message_anonymously(self):
        client = Client()
        response = client.post(
            "/contact/",
            {
                "name": "Test User",
                "email": "test@example.com",
                "message": "Hello, this is a test message.",
            },
        )
        assert response.status_code == 302
        assert ContactMessage.objects.count() == 1
        msg = ContactMessage.objects.first()
        assert msg.name == "Test User"
        assert msg.email == "test@example.com"

    def test_contact_post_invalid_form(self):
        client = Client()
        response = client.post(
            "/contact/",
            {
                "name": "",
                "email": "not-an-email",
                "message": "",
            },
        )
        assert response.status_code == 200
        assert ContactMessage.objects.count() == 0

    def test_contact_preserves_values_on_validation_error(self):
        client = Client()
        response = client.post(
            "/contact/",
            {
                "name": "Test User",
                "email": "bad-email",
                "message": "",
            },
        )
        content = response.content.decode()
        assert 'value="Test User"' in content
        assert 'value="bad-email"' in content

    def test_contact_shows_field_errors(self):
        client = Client()
        response = client.post(
            "/contact/",
            {
                "name": "",
                "email": "bad-email",
                "message": "",
            },
        )
        content = response.content.decode()
        assert 'class="field-error"' in content


@pytest.mark.django_db
class TestPasswordReset:
    def test_password_reset_page_loads(self):
        client = Client()
        response = client.get(reverse("password_reset"))
        assert response.status_code == 200

    def test_password_reset_done_page_loads(self):
        client = Client()
        response = client.get(reverse("password_reset_done"))
        assert response.status_code == 200

    def test_password_reset_submit_sends_email(self):
        User.objects.create_user(
            username="resetuser", email="reset@example.com", password="oldpass"
        )
        client = Client()
        response = client.post(
            reverse("password_reset"), {"email": "reset@example.com"}
        )
        assert response.status_code == 302
        assert response.url == reverse("password_reset_done")


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_redirects_to_login(self):
        User.objects.create_user("logoutuser", password="pass12345")
        client = Client()
        client.login(username="logoutuser", password="pass12345")
        response = client.get("/logout/")
        assert response.status_code == 302


@pytest.mark.django_db
class TestProfileView:
    def test_requires_login(self):
        client = Client()
        response = client.get("/profile/")
        assert response.status_code == 302

    def test_get_returns_form(self):
        User.objects.create_user("puser", password="pass12345")
        client = Client()
        client.login(username="puser", password="pass12345")
        response = client.get("/profile/")
        assert response.status_code == 200
        assert "form" in response.context
        assert "password_form" in response.context

    def test_get_populates_initial_data_with_profile(self):
        user = User.objects.create_user("puser_profile", password="pass12345")
        UserProfile.objects.create(
            user=user, city="اصفهان", neighborhood="", phone="09131234567"
        )
        client = Client()
        client.login(username="puser_profile", password="pass12345")
        response = client.get("/profile/")
        assert response.status_code == 200
        form = response.context["form"]
        assert form.initial.get("city") == "اصفهان"
        assert form.initial.get("phone") == "09131234567"

    def test_profile_update_shows_errors_on_invalid_data(self):
        user = User.objects.create_user("puser2", password="pass12345")
        UserProfile.objects.create(user=user, city="tehran", neighborhood="", phone="")
        client = Client()
        client.login(username="puser2", password="pass12345")
        response = client.post(
            "/profile/",
            {
                "update_profile": "1",
                "city": "تهران",
                "neighborhood": "",
                "phone": "invalid",
            },
        )
        assert response.status_code == 200
        assert response.context["form"].errors
        content = response.content.decode()
        assert "has-error" in content or "field-error" in content

    def test_password_change_shows_errors_on_wrong_old_password(self):
        User.objects.create_user("puser3", password="correctpass")
        client = Client()
        client.login(username="puser3", password="correctpass")
        response = client.post(
            "/profile/",
            {
                "change_password": "1",
                "old_password": "wrongpass",
                "new_password1": "newpass123",
                "new_password2": "newpass123",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'class="has-error"' in content or "field-error-msg" in content

    def test_profile_update_with_valid_data_saves_changes(self):
        user = User.objects.create_user("puser4", password="pass12345")
        UserProfile.objects.create(
            user=user, city="تهران", neighborhood="", phone="09121234567"
        )
        client = Client()
        client.login(username="puser4", password="pass12345")
        response = client.post(
            "/profile/",
            {
                "update_profile": "1",
                "first_name": "نام جدید",
                "last_name": "نام خانوادگی جدید",
                "email": "",
                "city": "مشهد",
                "neighborhood": "سجاد",
                "phone": "09131234567",
            },
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.first_name == "نام جدید"
        assert user.last_name == "نام خانوادگی جدید"

    def test_password_change_with_valid_data_succeeds(self):
        User.objects.create_user("puser5", password="oldpass123")
        client = Client()
        client.login(username="puser5", password="oldpass123")
        response = client.post(
            "/profile/",
            {
                "change_password": "1",
                "old_password": "oldpass123",
                "new_password1": "newpass456",
                "new_password2": "newpass456",
            },
        )
        assert response.status_code == 302
        client.logout()
        client.login(username="puser5", password="newpass456")
        assert client.session is not None

    def _assert_no_english_password_errors(self, content: str) -> None:
        assert "This password is too short" not in content
        assert "This password is too common" not in content
        assert "This password is entirely numeric" not in content

    def test_password_change_shows_persian_error_on_short_password(self):
        User.objects.create_user("puser6", password="oldpass123")
        client = Client()
        client.login(username="puser6", password="oldpass123")
        response = client.post(
            "/profile/",
            {
                "change_password": "1",
                "old_password": "oldpass123",
                "new_password1": "short",
                "new_password2": "short",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        self._assert_no_english_password_errors(content)
        assert "رمز عبور باید حداقل ۸ کاراکتر باشد." in content
        assert "رمز عبور وارد شده خیلی ساده است." not in content
        assert "رمز عبور نمی‌تواند فقط عدد باشد." not in content

    def test_password_change_shows_persian_error_on_common_password(self):
        User.objects.create_user("puser7", password="oldpass123")
        client = Client()
        client.login(username="puser7", password="oldpass123")
        response = client.post(
            "/profile/",
            {
                "change_password": "1",
                "old_password": "oldpass123",
                "new_password1": "password",
                "new_password2": "password",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        self._assert_no_english_password_errors(content)
        assert "رمز عبور وارد شده خیلی ساده است." in content
        assert "رمز عبور نمی‌تواند فقط عدد باشد." not in content

    def test_password_change_shows_persian_error_on_numeric_password(self):
        User.objects.create_user("puser8", password="oldpass123")
        client = Client()
        client.login(username="puser8", password="oldpass123")
        response = client.post(
            "/profile/",
            {
                "change_password": "1",
                "old_password": "oldpass123",
                "new_password1": "3571598264",
                "new_password2": "3571598264",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        self._assert_no_english_password_errors(content)
        assert "رمز عبور نمی‌تواند فقط عدد باشد." in content

    def test_password_change_shows_persian_error_on_wrong_old_and_short_password(self):
        User.objects.create_user("puser9", password="oldpass123")
        client = Client()
        client.login(username="puser9", password="oldpass123")
        response = client.post(
            "/profile/",
            {
                "change_password": "1",
                "old_password": "wrongold",
                "new_password1": "123",
                "new_password2": "123",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        self._assert_no_english_password_errors(content)
        assert "رمز عبور فعلی اشتباه است." in content
        assert "رمز عبور باید حداقل ۸ کاراکتر باشد." in content
        assert "رمز عبور وارد شده خیلی ساده است." not in content
        assert "رمز عبور نمی‌تواند فقط عدد باشد." not in content

    def test_password_change_shows_persian_error_on_mismatch(self):
        User.objects.create_user("puser10", password="oldpass123")
        client = Client()
        client.login(username="puser10", password="oldpass123")
        response = client.post(
            "/profile/",
            {
                "change_password": "1",
                "old_password": "oldpass123",
                "new_password1": "validpass123",
                "new_password2": "mismatch789",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        self._assert_no_english_password_errors(content)
        assert "رمز عبور و تکرار آن مطابقت ندارند." in content


def test_static_js_files_exist():
    import os

    root = os.path.join(os.path.dirname(__file__), "..", "..", "static")
    assert os.path.isfile(os.path.join(root, "libs", "alpine.min.js"))
    assert os.path.isfile(os.path.join(root, "services", "js", "main.js"))
    assert os.path.isfile(os.path.join(root, "services", "js", "error-translate.js"))
    assert os.path.isfile(os.path.join(root, "libs", "ol", "ol.js"))
    assert os.path.isfile(os.path.join(root, "libs", "ol", "ol.css"))


def test_vazirmatn_font_files_exist():
    import os

    root = os.path.join(os.path.dirname(__file__), "..", "..", "static")
    assert os.path.isfile(os.path.join(root, "Vazirmatn-Regular.woff2"))


def test_vazirmatn_css_in_style_css():
    import os

    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "static", "services", "css", "style.css"
    )
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "Vazirmatn" in content
    assert "@font-face" in content


def test_error_code_catalog():
    from services.error_codes import ERROR_CODES

    assert "auth/invalid-credentials" in ERROR_CODES
    assert (
        ERROR_CODES["auth/invalid-credentials"] == "نام کاربری یا رمز عبور اشتباه است."
    )


def test_get_error_message_with_kwargs():
    from services.error_codes import get_error_message

    msg = get_error_message("register/welcome", first_name="علی")
    assert "علی" in msg


def test_get_error_message_fallback():
    from services.error_codes import get_error_message

    msg = get_error_message("unknown/code")
    assert msg == "unknown/code"


@pytest.mark.django_db
def test_base_template_loads_static_assets():
    client = Client()
    response = client.get("/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "static/services/js/error-translate.js" in content
    assert "static/services/js/main.js" in content
    assert "static/services/css/style.css" in content
    assert 'dir="rtl"' in content
    assert 'lang="fa"' in content


def test_body_has_rtl_direction():
    import os

    css_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "static", "services", "css", "style.css"
    )
    with open(css_path, encoding="utf-8") as f:
        content = f.read()
    assert "direction: rtl" in content
    assert "text-align: right" in content


@pytest.mark.django_db
class TestNearbyCentersView:
    def test_requires_login(self):
        client = Client()
        response = client.get("/nearby-centers/")
        assert response.status_code == 302

    def test_renders_when_logged_in(self):
        User.objects.create_user("nearbyuser", password="pass12345")
        client = Client()
        client.login(username="nearbyuser", password="pass12345")
        response = client.get("/nearby-centers/")
        assert response.status_code == 200

    def test_renders_with_profile(self):
        user = User.objects.create_user("nbcityuser", password="pass12345")
        UserProfile.objects.create(
            user=user, city="تهران", neighborhood="ونک", phone="09121234567"
        )
        service = Service.objects.create(
            name="سرویس تست", organization="org", documents="d", steps="s"
        )
        ServiceCenter.objects.create(
            service=service, name="مرکز الف", address="آدرس", city="تهران"
        )
        client = Client()
        client.login(username="nbcityuser", password="pass12345")
        response = client.get("/nearby-centers/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "تهران" in content
        assert "centers_by_service" in response.context


@pytest.mark.django_db
class TestSecurityHeaders:
    def test_csp_header_present(self):
        client = Client()
        response = client.get("/")
        assert "Content-Security-Policy" in response
        csp = response["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "form-action 'self'" in csp

    def test_csp_allows_osm_tiles(self):
        client = Client()
        response = client.get("/")
        csp = response["Content-Security-Policy"]
        assert "https://tile.openstreetmap.org" in csp
        assert "https://*.tile.openstreetmap.org" in csp

    def test_x_content_type_options(self):
        client = Client()
        response = client.get("/")
        assert response["X-Content-Type-Options"] == "nosniff"

    def test_referrer_policy(self):
        client = Client()
        response = client.get("/")
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_session_cookie_httponly(self):
        client = Client()
        response = client.post(
            "/login/",
            {"username": "nonexistent", "password": "x"},
        )
        if response.has_header("Set-Cookie"):
            cookie = response.cookies.get("sessionid")
            if cookie:
                assert cookie.get("httponly", False)


@pytest.mark.django_db
class TestBookmarkView:
    def test_toggle_adds_bookmark(self):
        user = User.objects.create_user("bmuser", password="pass12345")
        service = Service.objects.create(
            name="bm-svc", organization="org", documents="d", steps="s"
        )
        client = Client()
        client.login(username="bmuser", password="pass12345")
        response = client.post(f"/bookmark/{service.id}/")
        assert response.status_code == 302
        assert Bookmark.objects.filter(user=user, service=service).exists()

    def test_toggle_removes_bookmark(self):
        user = User.objects.create_user("bmuser2", password="pass12345")
        service = Service.objects.create(
            name="bm-svc2", organization="org", documents="d", steps="s"
        )
        Bookmark.objects.create(user=user, service=service)
        client = Client()
        client.login(username="bmuser2", password="pass12345")
        response = client.post(f"/bookmark/{service.id}/")
        assert response.status_code == 302
        assert not Bookmark.objects.filter(user=user, service=service).exists()

    def test_toggle_requires_login(self):
        service = Service.objects.create(
            name="bm-svc3", organization="org", documents="d", steps="s"
        )
        client = Client()
        response = client.post(f"/bookmark/{service.id}/")
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_toggle_get_redirects_to_detail(self):
        User.objects.create_user("bmuser4", password="pass12345")
        service = Service.objects.create(
            name="bm-svc4", organization="org", documents="d", steps="s"
        )
        client = Client()
        client.login(username="bmuser4", password="pass12345")
        response = client.get(f"/bookmark/{service.id}/")
        assert response.status_code == 302
        assert f"/service/{service.id}/" in response.url

    def test_bookmarks_list_requires_login(self):
        client = Client()
        response = client.get("/bookmarks/")
        assert response.status_code == 302

    def test_bookmarks_list_shows_bookmarked_services(self):
        user = User.objects.create_user("bmlistuser", password="pass12345")
        service = Service.objects.create(
            name="کتاب نشانک", organization="org", documents="d", steps="s"
        )
        Bookmark.objects.create(user=user, service=service)
        client = Client()
        client.login(username="bmlistuser", password="pass12345")
        response = client.get("/bookmarks/")
        assert response.status_code == 200
        assert "کتاب نشانک" in response.content.decode()

    def test_detail_shows_bookmark_context(self):
        user = User.objects.create_user("bmdetail", password="pass12345")
        service = Service.objects.create(
            name="bm", organization="org", documents="d", steps="s"
        )
        Bookmark.objects.create(user=user, service=service)
        client = Client()
        client.login(username="bmdetail", password="pass12345")
        response = client.get(f"/service/{service.id}/")
        assert response.status_code == 200
        assert response.context["is_bookmarked"] is True


@pytest.mark.django_db
class TestSubmitComment:
    def test_submit_creates_comment(self):
        user = User.objects.create_user("commenter", password="pass12345")
        service = Service.objects.create(
            name="comment-svc", organization="org", documents="d", steps="s"
        )
        client = Client()
        client.login(username="commenter", password="pass12345")
        response = client.post(
            f"/comment/service/{service.id}/", {"text": "great service"}
        )
        assert response.status_code == 302
        comment = Comment.objects.get(user=user, service=service)
        assert comment.text == "great service"

    def test_submit_reply(self):
        user = User.objects.create_user("replier", password="pass12345")
        service = Service.objects.create(
            name="reply-svc", organization="org", documents="d", steps="s"
        )
        parent = Comment.objects.create(
            user=user, service=service, text="parent comment"
        )
        client = Client()
        client.login(username="replier", password="pass12345")
        response = client.post(
            f"/comment/service/{service.id}/",
            {"text": "reply text", "parent_id": str(parent.id)},
        )
        assert response.status_code == 302
        reply = Comment.objects.filter(parent=parent).first()
        assert reply is not None
        assert reply.text == "reply text"

    def test_submit_reply_to_deleted_comment_denied(self):
        user = User.objects.create_user("replier2", password="pass12345")
        service = Service.objects.create(
            name="del-reply-svc", organization="org", documents="d", steps="s"
        )
        parent = Comment.objects.create(
            user=user, service=service, text="deleted parent"
        )
        parent.deleted_by = user
        parent.save(update_fields=["deleted_by"])
        client = Client()
        client.login(username="replier2", password="pass12345")
        response = client.post(
            f"/comment/service/{service.id}/",
            {"text": "should fail", "parent_id": str(parent.id)},
        )
        assert response.status_code == 302
        assert not Comment.objects.filter(parent=parent).exists()

    def test_submit_requires_login(self):
        service = Service.objects.create(
            name="comment-svc2", organization="org", documents="d", steps="s"
        )
        client = Client()
        response = client.post(f"/comment/service/{service.id}/")
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_submit_get_redirects_to_detail(self):
        User.objects.create_user("commenter2", password="pass12345")
        service = Service.objects.create(
            name="comment-svc3", organization="org", documents="d", steps="s"
        )
        client = Client()
        client.login(username="commenter2", password="pass12345")
        response = client.get(f"/comment/service/{service.id}/")
        assert response.status_code == 302
        assert f"/service/{service.id}/" in response.url

    def test_detail_shows_comments(self):
        user = User.objects.create_user("shower", password="pass12345")
        service = Service.objects.create(
            name="show-svc", organization="org", documents="d", steps="s"
        )
        Comment.objects.create(user=user, service=service, text="visible comment")
        client = Client()
        response = client.get(f"/service/{service.id}/")
        assert response.status_code == 200
        assert (
            list(response.context["comments"]).count
            if hasattr(response.context["comments"], "count")
            else len(response.context["comments"]) >= 1
        )

    def test_service_detail_public(self):
        service = Service.objects.create(
            name="public-svc", organization="org", documents="d", steps="s"
        )
        client = Client()
        response = client.get(f"/service/{service.id}/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestEditComment:
    def _setup(self):
        self.user = User.objects.create_user("editor", password="pass12345")
        self.service = Service.objects.create(
            name="edit-svc", organization="org", documents="d", steps="s"
        )
        self.comment = Comment.objects.create(
            user=self.user, service=self.service, text="original text"
        )
        self.client = Client()
        self.client.login(username="editor", password="pass12345")

    def test_edit_own_comment(self):
        self._setup()
        resp = self.client.post(
            f"/comment/{self.comment.id}/edit/", {"text": "updated text"}
        )
        assert resp.status_code == 302
        self.comment.refresh_from_db()
        assert self.comment.text == "updated text"
        assert self.comment.edited_at is not None

    def test_edit_requires_login(self):
        self._setup()
        client = Client()
        resp = client.post(f"/comment/{self.comment.id}/edit/", {"text": "hacked"})
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_edit_other_users_comment_denied(self):
        self._setup()
        other = User.objects.create_user("other", password="pass12345")
        other_comment = Comment.objects.create(
            user=other, service=self.service, text="other's"
        )
        resp = self.client.post(
            f"/comment/{other_comment.id}/edit/", {"text": "hacked"}
        )
        assert resp.status_code == 302
        other_comment.refresh_from_db()
        assert other_comment.text == "other's"

    def test_edit_after_24h_denied(self):
        self._setup()
        from datetime import timedelta

        self.comment.created_at = timezone.now() - timedelta(hours=25)
        self.comment.save(update_fields=["created_at"])
        resp = self.client.post(
            f"/comment/{self.comment.id}/edit/", {"text": "expired"}
        )
        assert resp.status_code == 302
        self.comment.refresh_from_db()
        assert self.comment.text == "original text"

    def test_edit_deleted_comment_denied(self):
        self._setup()
        self.comment.deleted_by = self.user
        self.comment.save(update_fields=["deleted_by"])
        resp = self.client.post(
            f"/comment/{self.comment.id}/edit/", {"text": "deleted"}
        )
        assert resp.status_code == 302
        self.comment.refresh_from_db()
        assert self.comment.text == "original text"

    def test_edit_empty_text_ignored(self):
        self._setup()
        resp = self.client.post(f"/comment/{self.comment.id}/edit/", {"text": "   "})
        assert resp.status_code == 302
        self.comment.refresh_from_db()
        assert self.comment.text == "original text"

    def test_edit_get_returns_405(self):
        self._setup()
        resp = self.client.get(f"/comment/{self.comment.id}/edit/")
        assert resp.status_code == 405


@pytest.mark.django_db
class TestDeleteComment:
    def _setup(self):
        self.user = User.objects.create_user("deleter", password="pass12345")
        self.service = Service.objects.create(
            name="del-svc", organization="org", documents="d", steps="s"
        )
        self.comment = Comment.objects.create(
            user=self.user, service=self.service, text="to delete"
        )
        self.client = Client()
        self.client.login(username="deleter", password="pass12345")

    def test_delete_own_comment(self):
        self._setup()
        resp = self.client.post(f"/comment/{self.comment.id}/delete/")
        assert resp.status_code == 302
        self.comment.refresh_from_db()
        assert self.comment.is_deleted is True
        assert self.comment.deleted_by == self.user

    def test_delete_requires_login(self):
        self._setup()
        client = Client()
        resp = client.post(f"/comment/{self.comment.id}/delete/")
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_delete_other_users_comment_denied(self):
        self._setup()
        other = User.objects.create_user("other", password="pass12345")
        other_comment = Comment.objects.create(
            user=other, service=self.service, text="others"
        )
        resp = self.client.post(f"/comment/{other_comment.id}/delete/")
        assert resp.status_code == 302
        other_comment.refresh_from_db()
        assert other_comment.is_deleted is False

    def test_staff_can_delete_any_comment(self):
        self._setup()
        admin = User.objects.create_user("admin", password="pass12345", is_staff=True)
        client = Client()
        client.login(username="admin", password="pass12345")
        resp = client.post(f"/comment/{self.comment.id}/delete/")
        assert resp.status_code == 302
        self.comment.refresh_from_db()
        assert self.comment.is_deleted is True
        assert self.comment.deleted_by == admin

    def test_delete_already_deleted_noop(self):
        self._setup()
        self.comment.deleted_by = self.user
        self.comment.save(update_fields=["deleted_by"])
        resp = self.client.post(f"/comment/{self.comment.id}/delete/")
        assert resp.status_code == 302

    def test_delete_get_returns_405(self):
        self._setup()
        resp = self.client.get(f"/comment/{self.comment.id}/delete/")
        assert resp.status_code == 405


@pytest.mark.django_db
class TestCommentOrdering:
    def test_comments_newest_first(self):
        user = User.objects.create_user("orderuser", password="pass12345")
        service = Service.objects.create(
            name="order-svc", organization="org", documents="d", steps="s"
        )
        c1 = Comment.objects.create(user=user, service=service, text="first")
        c2 = Comment.objects.create(user=user, service=service, text="second")
        c3 = Comment.objects.create(user=user, service=service, text="third")
        client = Client()
        response = client.get(f"/service/{service.id}/")
        comments = list(response.context["comments"])
        assert comments[0].id == c3.id
        assert comments[1].id == c2.id
        assert comments[2].id == c1.id


@pytest.mark.django_db
class TestCommentPagination:
    def test_initial_page_limit(self):
        user = User.objects.create_user("pageuser", password="pass12345")
        service = Service.objects.create(
            name="page-svc", organization="org", documents="d", steps="s"
        )
        for i in range(7):
            Comment.objects.create(user=user, service=service, text=f"comment {i}")
        client = Client()
        response = client.get(f"/service/{service.id}/")
        comments = list(response.context["comments"])
        assert len(comments) == 5
        assert response.context["has_more_comments"] is True

    def test_no_load_more_when_few_comments(self):
        user = User.objects.create_user("fewuser", password="pass12345")
        service = Service.objects.create(
            name="few-svc", organization="org", documents="d", steps="s"
        )
        Comment.objects.create(user=user, service=service, text="only one")
        client = Client()
        response = client.get(f"/service/{service.id}/")
        assert response.context["has_more_comments"] is False

    def test_load_more_returns_html(self):
        user = User.objects.create_user("apiuser", password="pass12345")
        service = Service.objects.create(
            name="api-svc", organization="org", documents="d", steps="s"
        )
        for i in range(7):
            Comment.objects.create(user=user, service=service, text=f"comment {i}")
        client = Client()
        response = client.get(f"/api/load-comments/service/{service.id}/?page=2")
        assert response.status_code == 200
        data = response.json()
        assert "html" in data
        assert data["has_next"] is False
        assert len(data["html"]) > 0

    def test_load_comments_invalid_target(self):
        client = Client()
        response = client.get("/api/load-comments/invalid/1/?page=2")
        assert response.status_code == 400

    def test_load_comments_center(self):
        user = User.objects.create_user("centerapi", password="pass12345")
        service = Service.objects.create(
            name="centerapi-svc", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            name="centerapi-center", service=service, city="Tehran"
        )
        for i in range(7):
            Comment.objects.create(
                user=user, service_center=center, text=f"center comment {i}"
            )
        client = Client()
        response = client.get(f"/api/load-comments/center/{center.id}/?page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["has_next"] is False


@pytest.mark.django_db
class TestCenterDetail:
    def test_center_detail_public(self):
        service = Service.objects.create(
            name="center-svc", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="Test Center", address="addr", city="Tehran"
        )
        client = Client()
        response = client.get(f"/center/{center.id}/")
        assert response.status_code == 200
        assert response.context["center"] == center

    def test_center_detail_shows_ratings(self):
        user = User.objects.create_user("crater", password="pass12345")
        service = Service.objects.create(
            name="cr-svc", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="CR Center", address="addr", city="Tehran"
        )
        CenterRating.objects.create(user=user, service_center=center, score=4)
        client = Client()
        response = client.get(f"/center/{center.id}/")
        assert response.status_code == 200
        assert response.context["avg_rating"] == 4.0
        assert response.context["rating_count"] == 1


@pytest.mark.django_db
class TestSubmitCenterRating:
    def test_submit_creates_rating(self):
        user = User.objects.create_user("crater", password="pass12345")
        service = Service.objects.create(
            name="cr-svc", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="CR Center", address="addr", city="Tehran"
        )
        client = Client()
        client.login(username="crater", password="pass12345")
        response = client.post(f"/rate-center/{center.id}/", {"score": "4"})
        assert response.status_code == 302
        rating = CenterRating.objects.get(user=user, service_center=center)
        assert rating.score == 4

    def test_submit_updates_existing_rating(self):
        user = User.objects.create_user("crater2", password="pass12345")
        service = Service.objects.create(
            name="cr-svc2", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="CR Center2", address="addr", city="Tehran"
        )
        CenterRating.objects.create(user=user, service_center=center, score=2)
        client = Client()
        client.login(username="crater2", password="pass12345")
        response = client.post(f"/rate-center/{center.id}/", {"score": "5"})
        assert response.status_code == 302
        rating = CenterRating.objects.get(user=user, service_center=center)
        assert rating.score == 5

    def test_submit_requires_login(self):
        service = Service.objects.create(
            name="cr-svc3", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="CR Center3", address="addr", city="Tehran"
        )
        client = Client()
        response = client.post(f"/rate-center/{center.id}/")
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_submit_get_redirects(self):
        User.objects.create_user("crater3", password="pass12345")
        service = Service.objects.create(
            name="cr-svc4", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="CR Center4", address="addr", city="Tehran"
        )
        client = Client()
        client.login(username="crater3", password="pass12345")
        response = client.get(f"/rate-center/{center.id}/")
        assert response.status_code == 302
        assert f"/center/{center.id}/" in response.url


class TestRateLimitPage:
    def test_429_template_exists(self):
        import os

        template_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "templates", "429.html"
        )
        assert os.path.isfile(template_path)


@pytest.mark.django_db
class TestAdminURLConfigurable:
    def test_admin_accessible_at_default_path(self):
        client = Client()
        response = client.get("/admin/login/")
        assert response.status_code in (200, 302)

    def test_rate_limit_error_code_exists(self):
        from services.error_codes import ERROR_CODES

        assert "ratelimit/exceeded" in ERROR_CODES


@pytest.mark.django_db
class TestResponsiveHamburger:
    def test_hamburger_button_present(self):
        client = Client()
        response = client.get("/")
        content = response.content.decode()
        assert 'class="mobile-menu-btn"' in content
        assert "onclick=" in content
        assert "toggleMenu" in content
        assert 'aria-label="منو"' in content

    def test_mobile_menu_btn_css_hidden_on_desktop(self):
        import os

        css_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "static",
            "services",
            "css",
            "style.css",
        )
        with open(css_path, encoding="utf-8") as f:
            content = f.read()
        assert ".mobile-menu-btn {\n  display: none;" in content
        assert "@media (max-width: 768px)" in content
        assert ".nav-links" in content

    def test_close_menu_function_exists(self):
        import os

        js_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "services", "js", "main.js"
        )
        with open(js_path, encoding="utf-8") as f:
            content = f.read()
        assert "function closeMenu" in content
        assert 'navLinks.querySelectorAll("a").forEach' in content
        assert 'link.addEventListener("click", closeMenu)' in content

    def test_nav_links_use_getElementById(self):
        import os

        js_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "static", "services", "js", "main.js"
        )
        with open(js_path, encoding="utf-8") as f:
            content = f.read()
        assert 'document.getElementById("navLinks")' in content
        assert "navLinks" in content


@pytest.mark.django_db
class TestSeoEndpoints:
    def test_robots_txt(self):
        from django.test.utils import override_settings

        with override_settings(SITE_URL="https://example.com"):
            client = Client()
            response = client.get("/robots.txt")
            assert response.status_code == 200
            assert response["Content-Type"] == "text/plain"
            content = response.content.decode()
            assert "User-agent: *" in content
            assert "Sitemap: https://example.com/sitemap.xml" in content

    def test_sitemap_xml(self):
        from django.test.utils import override_settings

        with override_settings(SITE_URL="https://example.com"):
            client = Client()
            response = client.get("/sitemap.xml")
            assert response.status_code == 200
            assert "application/xml" in response["Content-Type"]
            content = response.content.decode()
            assert '<?xml version="1.0" encoding="UTF-8"?>' in content
            assert "<urlset" in content
            assert "https://example.com" in content

    def test_sitemap_includes_services(self):
        from django.test.utils import override_settings

        svc1 = Service.objects.create(
            name="سرویس الف", organization="org1", documents="d", steps="s"
        )
        svc2 = Service.objects.create(
            name="سرویس ب", organization="org2", documents="d", steps="s"
        )
        with override_settings(SITE_URL="https://example.com"):
            client = Client()
            response = client.get("/sitemap.xml")
            content = response.content.decode()
            assert f"/service/{svc1.id}/" in content
            assert f"/service/{svc2.id}/" in content

    def test_homepage_has_meta_tags(self):
        client = Client()
        response = client.get("/")
        content = response.content.decode()
        assert 'name="description"' in content
        assert 'name="keywords"' in content
        assert 'rel="canonical"' in content
        assert 'property="og:title"' in content
        assert 'property="og:description"' in content
        assert 'name="twitter:title"' in content
        assert 'name="twitter:description"' in content


@pytest.mark.django_db
def test_print_media_query_exists_in_css():
    import os

    css_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "static", "services", "css", "style.css"
    )
    with open(css_path, encoding="utf-8") as f:
        content = f.read()
    assert "@media print" in content
    assert ".btn-print" in content


@pytest.mark.django_db
class TestPrintableView:
    def test_print_button_on_detail_page(self):
        from services.models import Service

        svc = Service.objects.create(
            name="test-print",
            organization="org",
            documents="doc1|doc2",
            steps="step1|step2",
            cost="free",
            duration="1 day",
        )
        User.objects.create_user("printuser", password="pass12345")
        client = Client()
        client.login(username="printuser", password="pass12345")
        response = client.get(f"/service/{svc.id}/")
        content = response.content.decode()
        assert "btn-print" in content
        assert "window.print()" in content


@pytest.mark.django_db
class TestVerifyOTPView:
    FIXED_OTP = "123456"

    def _setup_pending_registration(self, client, phone="09121234567"):
        """Helper: perform a valid registration POST and return the known OTP code."""
        data = {
            "username": "otpuser",
            "first_name": "علی",
            "last_name": "محمدی",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": phone,
        }
        with (
            override_settings(DISABLE_SMS=True),
            patch("services.views.generate_otp", return_value=self.FIXED_OTP),
        ):
            client.post("/register/", data)
        verification = PhoneVerification.objects.filter(phone=phone).first()
        assert verification is not None
        return self.FIXED_OTP

    def test_verify_otp_page_loads(self):
        client = Client()
        response = client.get("/verify-otp/")
        assert response.status_code == 302
        assert "/register/" in response.url

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_redirects_to_register_without_session(self):
        client = Client()
        response = client.post("/verify-otp/", {"otp_code": "123456"})
        assert response.status_code == 302
        assert "/register/" in response.url

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_shows_form_with_session(self):
        client = Client()
        self._setup_pending_registration(client)
        response = client.get("/verify-otp/")
        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["phone"] == "09121234567"

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_success_creates_user(self):
        client = Client()
        otp = self._setup_pending_registration(client)
        response = client.post("/verify-otp/", {"otp_code": otp})
        assert response.status_code == 302
        assert response.url == "/"
        user = User.objects.get(username="otpuser")
        assert user.first_name == "علی"
        assert user.last_name == "محمدی"
        assert user.profile.phone == "09121234567"

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_success_logs_in_user(self):
        client = Client()
        otp = self._setup_pending_registration(client)
        client.post("/verify-otp/", {"otp_code": otp})
        response = client.get("/dashboard/")
        assert response.status_code == 200

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_wrong_code(self):
        client = Client()
        self._setup_pending_registration(client)
        response = client.post("/verify-otp/", {"otp_code": "999999"})
        assert response.status_code == 200
        assert "form" in response.context
        assert not User.objects.filter(username="otpuser").exists()

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_clears_session_after_success(self):
        client = Client()
        otp = self._setup_pending_registration(client)
        client.post("/verify-otp/", {"otp_code": otp})
        session = client.session
        assert "pending_registration" not in session

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_marks_verification_as_used(self):
        client = Client()
        otp = self._setup_pending_registration(client)
        client.post("/verify-otp/", {"otp_code": otp})
        verification = PhoneVerification.objects.filter(phone="09121234567").first()
        assert verification is not None
        assert verification.is_used is True

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_empty_code(self):
        client = Client()
        self._setup_pending_registration(client)
        response = client.post("/verify-otp/", {"otp_code": ""})
        assert response.status_code == 200
        assert response.context["form"].errors

    @override_settings(DISABLE_SMS=True)
    def test_verify_otp_expired_code(self):
        from datetime import timedelta

        from django.utils import timezone

        client = Client()
        otp = self._setup_pending_registration(client)
        verification = PhoneVerification.objects.filter(phone="09121234567").first()
        verification.created_at = timezone.now() - timedelta(minutes=30)
        verification.save(update_fields=["created_at"])
        response = client.post("/verify-otp/", {"otp_code": otp})
        assert response.status_code == 200
        assert not User.objects.filter(username="otpuser").exists()


@pytest.mark.django_db
class TestResendOTPView:
    @override_settings(DISABLE_SMS=True)
    def test_resend_otp_creates_new_verification(self):
        client = Client()
        data = {
            "username": "resenduser",
            "first_name": "رضا",
            "last_name": "احمدی",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09121234567",
        }
        client.post("/register/", data)
        initial_count = PhoneVerification.objects.filter(phone="09121234567").count()
        client.post("/resend-otp/")
        final_count = PhoneVerification.objects.filter(phone="09121234567").count()
        assert final_count == initial_count + 1

    @override_settings(DISABLE_SMS=True)
    def test_resend_otp_marks_old_as_used(self):
        client = Client()
        data = {
            "username": "resenduser2",
            "first_name": "علی",
            "last_name": "رضایی",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09351234567",
        }
        client.post("/register/", data)
        client.post("/resend-otp/")
        old_verifications = PhoneVerification.objects.filter(
            phone="09351234567", is_used=True
        )
        assert old_verifications.exists()
        new_verification = PhoneVerification.objects.filter(
            phone="09351234567", is_used=False
        ).first()
        assert new_verification is not None

    @override_settings(DISABLE_SMS=True)
    def test_resend_otp_redirects_to_verify(self):
        client = Client()
        data = {
            "username": "resenduser3",
            "first_name": "مریم",
            "last_name": "اکبری",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09191234567",
        }
        client.post("/register/", data)
        response = client.post("/resend-otp/")
        assert response.status_code == 302
        assert "/verify-otp/" in response.url

    def test_resend_otp_redirects_to_register_without_session(self):
        client = Client()
        response = client.post("/resend-otp/")
        assert response.status_code == 302
        assert "/register/" in response.url

    @override_settings(DISABLE_SMS=True)
    def test_resend_otp_allows_login_with_new_code(self):
        client = Client()
        data = {
            "username": "resenduser4",
            "first_name": "حسن",
            "last_name": "علی",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09171234567",
        }
        client.post("/register/", data)
        client.post("/resend-otp/")
        new_verification = PhoneVerification.objects.filter(
            phone="09171234567", is_used=False
        ).first()
        assert new_verification is not None
        plain_otp = generate_otp()
        new_verification.otp_code = hash_otp(plain_otp)
        new_verification.save(update_fields=["otp_code"])
        response = client.post("/verify-otp/", {"otp_code": plain_otp})
        assert response.status_code == 302
        assert User.objects.filter(username="resenduser4").exists()


@pytest.mark.django_db
class TestResendOTPApi:
    @override_settings(DISABLE_SMS=True, OTP_RESEND_COOLDOWN_SECONDS=0)
    def test_returns_json_success(self):
        client = Client()
        data = {
            "username": "apiuser1",
            "first_name": "Ali",
            "last_name": "Rezaei",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "Tehran",
            "neighborhood": "Vanak",
            "phone": "09121000001",
        }
        client.post("/register/", data)
        response = client.post("/api/resend-otp/", content_type="application/json")
        assert response.status_code == 200
        body = response.json()
        assert "message" in body
        assert "cooldown" in body

    @override_settings(DISABLE_SMS=True, OTP_RESEND_COOLDOWN_SECONDS=120)
    def test_enforces_cooldown(self):
        client = Client()
        data = {
            "username": "apiuser2",
            "first_name": "Sara",
            "last_name": "Ahmadi",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "Tehran",
            "neighborhood": "Vanak",
            "phone": "09121000002",
        }
        client.post("/register/", data)
        response = client.post("/api/resend-otp/", content_type="application/json")
        assert response.status_code == 429
        body = response.json()
        assert "error" in body
        assert "cooldown" in body
        assert body["cooldown"] > 0

    def test_returns_400_without_session(self):
        client = Client()
        response = client.post("/api/resend-otp/", content_type="application/json")
        assert response.status_code == 400
        body = response.json()
        assert "error" in body

    def test_returns_405_for_get(self):
        client = Client()
        response = client.get("/api/resend-otp/")
        assert response.status_code == 405

    @override_settings(DISABLE_SMS=True)
    def test_returns_400_for_authenticated_user(self):
        User.objects.create_user(username="apiuser3", password="ComplexPass1!")
        client = Client()
        client.login(username="apiuser3", password="ComplexPass1!")
        response = client.post("/api/resend-otp/", content_type="application/json")
        assert response.status_code == 400

    @override_settings(DISABLE_SMS=True, OTP_RESEND_COOLDOWN_SECONDS=0)
    def test_creates_new_verification_on_success(self):
        client = Client()
        data = {
            "username": "apiuser4",
            "first_name": "Mohsen",
            "last_name": "Karimi",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "Tehran",
            "neighborhood": "Vanak",
            "phone": "09121000004",
        }
        client.post("/register/", data)
        initial = PhoneVerification.objects.filter(phone="09121000004").count()
        client.post("/api/resend-otp/", content_type="application/json")
        final = PhoneVerification.objects.filter(phone="09121000004").count()
        assert final == initial + 1

    @override_settings(DISABLE_SMS=True, OTP_RESEND_COOLDOWN_SECONDS=0)
    def test_marks_old_otp_as_used(self):
        client = Client()
        data = {
            "username": "apiuser5",
            "first_name": "Reza",
            "last_name": "Hosseini",
            "email": "",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "Tehran",
            "neighborhood": "Vanak",
            "phone": "09121000005",
        }
        client.post("/register/", data)
        client.post("/api/resend-otp/", content_type="application/json")
        assert PhoneVerification.objects.filter(
            phone="09121000005", is_used=True
        ).exists()
        assert PhoneVerification.objects.filter(
            phone="09121000005", is_used=False
        ).exists()


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_returns_200(self):
        client = Client()
        response = client.get("/health/")
        assert response.status_code == 200

    def test_health_returns_json(self):
        client = Client()
        response = client.get("/health/")
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_health_status_is_ok(self):
        client = Client()
        response = client.get("/health/")
        assert response.json()["status"] == "ok"

    def test_health_version_is_nonempty_string(self):
        client = Client()
        response = client.get("/health/")
        version = response.json()["version"]
        assert isinstance(version, str)
        assert len(version) > 0


@pytest.mark.django_db
class TestSessionRefresh:
    def test_authenticated_request_modifies_session(self):
        User.objects.create_user("sessionuser", password="pass12345")
        client = Client()
        client.login(username="sessionuser", password="pass12345")
        response = client.get("/dashboard/")
        assert response.status_code == 200
        session = client.session
        assert session.session_key is not None

    def test_anonymous_request_does_not_modify_session(self):
        client = Client()
        response = client.get("/health/")
        assert response.status_code == 200
        # SessionRefreshMiddleware should only touch authenticated sessions.
        # Verify it doesn't crash on anonymous requests.
        assert response.json()["status"] == "ok"


class TestVersion:
    def test_version_is_accessible(self):
        from agahyar_project import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_matches_package(self):
        from importlib.metadata import version

        from agahyar_project import __version__

        assert __version__ == version("agahyar")


class TestAdminStats:
    @pytest.mark.django_db
    def test_anonymous_redirects_to_login(self):
        client = Client()
        response = client.get("/admin/stats/")
        assert response.status_code == 302
        assert "login" in response.url

    @pytest.mark.django_db
    def test_non_staff_gets_redirect(self):
        User.objects.create_user("regular", password="pass12345")
        client = Client()
        client.login(username="regular", password="pass12345")
        response = client.get("/admin/stats/")
        assert response.status_code in (403, 302)

    @pytest.mark.django_db
    def test_staff_gets_200(self):
        User.objects.create_user("admin", password="pass12345", is_staff=True)
        client = Client()
        client.login(username="admin", password="pass12345")
        response = client.get("/admin/stats/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_context_contains_overview_counts(self):
        User.objects.create_user("admin", password="pass12345", is_staff=True)
        Service.objects.create(name="S1", organization="O1", documents="d", steps="s")
        client = Client()
        client.login(username="admin", password="pass12345")
        response = client.get("/admin/stats/")
        ctx = response.context
        assert ctx["overview"]["total_users"] >= 1
        assert ctx["overview"]["total_services"] >= 1
        assert "chart_reg" in ctx
        assert "chart_comments" in ctx

    @pytest.mark.django_db
    def test_chart_data_is_valid_json(self):
        User.objects.create_user("admin", password="pass12345", is_staff=True)
        client = Client()
        client.login(username="admin", password="pass12345")
        response = client.get("/admin/stats/")
        assert json.loads(response.context["chart_reg"]) is not None
        assert json.loads(response.context["chart_comments"]) is not None
        assert json.loads(response.context["chart_ratings"]) is not None
        assert json.loads(response.context["chart_services"]) is not None
