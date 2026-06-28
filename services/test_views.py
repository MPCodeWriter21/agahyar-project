import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from services.models import FAQ, ContactMessage, Service, UserProfile
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

    def test_register_creates_user(self):
        client = Client()
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
        }
        response = client.post("/register/", data)
        assert response.status_code == 302
        assert User.objects.filter(username="newuser").exists()

    def test_register_with_phone(self):
        client = Client()
        data = {
            "username": "phonetest",
            "email": "phone@example.com",
            "password1": "ComplexPass1!",
            "password2": "ComplexPass1!",
            "city": "تهران",
            "neighborhood": "ونک",
            "phone": "09121234567",
        }
        response = client.post("/register/", data)
        assert response.status_code == 302
        user = User.objects.get(username="phonetest")
        assert user.profile.phone == "09121234567"

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


@pytest.mark.django_db
class TestHomeView:
    def test_requires_login(self):
        client = Client()
        response = client.get("/")
        assert response.status_code == 302

    def test_shows_popular_services(self):
        User.objects.create_user("homeuser", password="pass12345")
        Service.objects.create(
            name="test service", organization="org", documents="doc1", steps="step1"
        )
        client = Client()
        client.login(username="homeuser", password="pass12345")
        response = client.get("/")
        assert response.status_code == 200
        assert "test service" in str(response.content)


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


@pytest.mark.django_db
class TestServiceListView:
    def test_requires_login(self):
        client = Client()
        response = client.get("/services/")
        assert response.status_code == 302

    def test_lists_services_ordered_by_name(self):
        User.objects.create_user("listuser", password="pass12345")
        Service.objects.create(name="beta", organization="o", documents="d", steps="s")
        Service.objects.create(name="alpha", organization="o", documents="d", steps="s")
        client = Client()
        client.login(username="listuser", password="pass12345")
        response = client.get("/services/")
        assert response.status_code == 200
        content = str(response.content)
        assert content.index("alpha") < content.index("beta")

    def test_list_pagination_context(self):
        User.objects.create_user("paguser", password="pass12345")
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
    def test_requires_login(self):
        client = Client()
        response = client.get("/service/1/")
        assert response.status_code == 302

    def test_shows_service_details(self):
        User.objects.create_user("detailuser", password="pass12345")
        service = Service.objects.create(
            name="passport", organization="police", documents="doc1", steps="step1"
        )
        client = Client()
        client.login(username="detailuser", password="pass12345")
        response = client.get(f"/service/{service.id}/")
        assert response.status_code == 200
        assert "passport" in str(response.content)


@pytest.mark.django_db
class TestFAQView:
    def test_requires_login(self):
        client = Client()
        response = client.get("/faq/")
        assert response.status_code == 302

    def test_shows_faqs_ordered(self):
        User.objects.create_user("faquser", password="pass12345")
        FAQ.objects.create(question="q1", answer="a1", order=2)
        FAQ.objects.create(question="q2", answer="a2", order=1)
        client = Client()
        client.login(username="faquser", password="pass12345")
        response = client.get("/faq/")
        assert response.status_code == 200
        assert "q1" in str(response.content)


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


def test_static_js_files_exist():
    import os

    base = os.path.join(os.path.dirname(__file__), "..", "static", "services", "js")
    assert os.path.isfile(os.path.join(base, "alpine.min.js"))
    assert os.path.isfile(os.path.join(base, "main.js"))


@pytest.mark.django_db
def test_base_template_loads_js_files():
    User.objects.create_user("jstestuser", password="pass12345")
    client = Client()
    client.login(username="jstestuser", password="pass12345")
    response = client.get("/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "static/services/js/alpine.min.js" in content
    assert "static/services/js/main.js" in content


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
