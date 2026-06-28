import pytest
from django.contrib.auth.models import User
from django.test import Client

from services.forms import CITY_CHOICES, LoginForm, RegisterForm


class TestCityChoices:
    def test_city_choices_has_placeholder_first(self):
        assert CITY_CHOICES[0] == ("", "شهر خود را انتخاب کنید")

    def test_city_choices_contains_tehran(self):
        assert ("تهران", "تهران") in CITY_CHOICES

    def test_city_choices_count(self):
        assert len(CITY_CHOICES) == 13

    def test_register_form_uses_city_choices(self):
        form = RegisterForm()
        city_field = form.fields["city"]
        widget = city_field.widget
        assert widget.choices == CITY_CHOICES


@pytest.mark.django_db
class TestRegisterForm:
    def test_form_renders_city_field(self):
        form = RegisterForm()
        html = str(form.as_p())
        assert "تهران" in html
        assert "مشهد" in html

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


class TestLoginForm:
    def test_valid_form(self):
        form = LoginForm(data={"username": "testuser", "password": "secret123"})
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
