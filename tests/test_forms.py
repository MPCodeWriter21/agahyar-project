"""Tests for the Agahyar form classes.

Validates city choices structure, field presence, duplicate
detection (username, email, phone), and login/registration
form behavior.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from services.forms import LoginForm, ProfileForm, RegisterForm, get_city_choices
from services.models import Service, ServiceCenter, UserProfile


class TestCityChoices:
    @pytest.mark.django_db
    def test_city_choices_has_placeholder_first(self):
        choices = get_city_choices()
        assert choices[0] == ("", "شهر خود را انتخاب کنید")

    @pytest.mark.django_db
    def test_city_choices_contains_db_cities(self):
        svc = Service.objects.create(
            name="test", organization="o", documents="d", steps="s"
        )
        ServiceCenter.objects.create(
            name="مرکز الف",
            service=svc,
            city="تهران",
        )
        choices = get_city_choices()
        city_values = [c for c, _ in choices[1:]]
        assert "تهران" in city_values

    @pytest.mark.django_db
    def test_city_choices_are_dynamic(self):
        svc = Service.objects.create(
            name="test2", organization="o", documents="d", steps="s"
        )
        ServiceCenter.objects.create(
            name="مرکز ب",
            service=svc,
            city="اصفهان",
        )
        choices = get_city_choices()
        city_values = [c for c, _ in choices[1:]]
        assert "اصفهان" in city_values

    @pytest.mark.django_db
    def test_register_form_uses_dynamic_choices(self):
        svc = Service.objects.create(
            name="test3", organization="o", documents="d", steps="s"
        )
        ServiceCenter.objects.create(
            name="مرکز ج",
            service=svc,
            city="شیراز",
        )
        form = RegisterForm()
        city_field = form.fields["city"]
        widget = city_field.widget
        city_values = [c for c, _ in widget.choices[1:]]
        assert "شیراز" in city_values


@pytest.mark.django_db
class TestRegisterForm:
    def test_form_renders_city_field(self):
        svc = Service.objects.create(
            name="test4", organization="o", documents="d", steps="s"
        )
        ServiceCenter.objects.create(name="مرکز تست", service=svc, city="تهران")
        form = RegisterForm()
        html = str(form.as_p())
        assert "تهران" in html
        assert "شهر محل سکونت" in html

    def test_form_has_phone_field(self):
        form = RegisterForm()
        assert "phone" in form.fields
        assert form.fields["phone"].required

    def test_form_has_first_name_field(self):
        form = RegisterForm()
        assert "first_name" in form.fields
        assert form.fields["first_name"].required

    def test_form_has_last_name_field(self):
        form = RegisterForm()
        assert "last_name" in form.fields
        assert form.fields["last_name"].required

    def test_form_email_optional(self):
        form = RegisterForm()
        assert "email" in form.fields
        assert not form.fields["email"].required

    def test_duplicate_username_error_in_persian(self):
        User.objects.create_user("existinguser", password="pass12345")
        form = RegisterForm(
            data={
                "username": "existinguser",
                "first_name": "علی",
                "last_name": "محمدی",
                "email": "",
                "password1": "ComplexPass1!",
                "password2": "ComplexPass1!",
                "city": "تهران",
                "neighborhood": "ونک",
                "phone": "09121234567",
            }
        )
        assert not form.is_valid()
        assert "username" in form.errors
        assert "قبلاً ثبت شده است" in form.errors["username"][0]

    def test_duplicate_email_raises_error(self):
        User.objects.create_user("user1", email="dup@test.com", password="pass12345")
        form = RegisterForm(
            data={
                "username": "newuser",
                "first_name": "علی",
                "last_name": "محمدی",
                "email": "dup@test.com",
                "password1": "ComplexPass1!",
                "password2": "ComplexPass1!",
                "city": "تهران",
                "neighborhood": "ونک",
                "phone": "09121234567",
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_duplicate_phone_raises_error(self):
        user = User.objects.create_user("user1", password="pass12345")
        UserProfile.objects.create(user=user, city="تهران", phone="09121234567")
        form = RegisterForm(
            data={
                "username": "newuser",
                "first_name": "علی",
                "last_name": "محمدی",
                "email": "",
                "password1": "ComplexPass1!",
                "password2": "ComplexPass1!",
                "city": "تهران",
                "neighborhood": "ونک",
                "phone": "09121234567",
            }
        )
        assert not form.is_valid()
        assert "phone" in form.errors

    def test_all_numeric_username_rejected(self):
        form = RegisterForm(
            data={
                "username": "12345678",
                "first_name": "علی",
                "last_name": "محمدی",
                "email": "",
                "password1": "ComplexPass1!",
                "password2": "ComplexPass1!",
                "city": "تهران",
                "neighborhood": "ونک",
                "phone": "09121234567",
            }
        )
        assert not form.is_valid()
        assert "username" in form.errors
        assert "فقط شامل عدد" in form.errors["username"][0]

    def test_at_in_username_rejected(self):
        form = RegisterForm(
            data={
                "username": "user@name",
                "first_name": "علی",
                "last_name": "محمدی",
                "email": "",
                "password1": "ComplexPass1!",
                "password2": "ComplexPass1!",
                "city": "تهران",
                "neighborhood": "ونک",
                "phone": "09121234567",
            }
        )
        assert not form.is_valid()
        assert "username" in form.errors
        assert "@" in form.errors["username"][0]


@pytest.mark.django_db
class TestProfileForm:
    def test_duplicate_phone_excludes_own_user(self):
        user = User.objects.create_user("user1", password="pass12345")
        UserProfile.objects.create(user=user, city="تهران", phone="09121234567")
        form = ProfileForm(
            data={
                "first_name": "علی",
                "last_name": "محمدی",
                "email": "",
                "city": "تهران",
                "neighborhood": "ونک",
                "phone": "09121234567",
            },
            user_id=user.id,
        )
        assert form.is_valid(), form.errors

    def test_duplicate_phone_rejects_other_user(self):
        user_a = User.objects.create_user("user_a", password="pass12345")
        UserProfile.objects.create(user=user_a, city="تهران", phone="09121234567")
        user_b = User.objects.create_user("user_b", password="pass12345")
        UserProfile.objects.create(user=user_b, city="مشهد", phone="09131234567")
        form = ProfileForm(
            data={
                "first_name": "رضا",
                "last_name": "احمدی",
                "email": "",
                "city": "تهران",
                "neighborhood": "",
                "phone": "09121234567",
            },
            user_id=user_b.id,
        )
        assert not form.is_valid()
        assert "phone" in form.errors


class TestLoginForm:
    def test_valid_form(self):
        form = LoginForm(
            data={"username": "testuser", "password": "secret123", "remember_me": True}
        )
        assert form.is_valid()

    def test_valid_form_remember_me_unchecked(self):
        form = LoginForm(
            data={"username": "testuser", "password": "secret123", "remember_me": False}
        )
        assert form.is_valid()

    def test_missing_username(self):
        form = LoginForm(data={"password": "secret123"})
        assert not form.is_valid()
        assert "username" in form.errors

    def test_missing_password(self):
        form = LoginForm(data={"username": "testuser"})
        assert not form.is_valid()
        assert "password" in form.errors


@pytest.mark.django_db
class TestLoginView:
    def test_get_returns_form(self):
        client = Client()
        response = client.get("/login/")
        assert response.status_code == 200
        assert "form" in response.context

    def test_login_with_valid_credentials(self):
        User.objects.create_user(username="testuser", password="secret123")
        client = Client()
        response = client.post(
            "/login/", {"username": "testuser", "password": "secret123"}
        )
        assert response.status_code == 302

    def test_login_with_invalid_credentials(self):
        client = Client()
        response = client.post("/login/", {"username": "noone", "password": "wrong"})
        assert response.status_code == 200
        assert "form" in response.context
