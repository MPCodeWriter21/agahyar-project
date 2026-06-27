import pytest
from django.test import Client
from django.contrib.auth.models import User
from services.models import Service, UserProfile, FAQ, ServiceCenter
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

    def test_register_requires_login_redirect_when_authenticated(self):
        User.objects.create_user("loggedin", password="pass12345")
        client = Client()
        client.login(username="loggedin", password="pass12345")
        response = client.get("/register/")
        assert response.status_code == 302


@pytest.mark.django_db
class TestHomeView:

    def test_requires_login(self):
        client = Client()
        response = client.get("/")
        assert response.status_code == 302

    def test_shows_popular_services(self):
        user = User.objects.create_user("homeuser", password="pass12345")
        Service.objects.create(name="test service", organization="org",
                               documents="doc1", steps="step1")
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
        user = User.objects.create_user("searchuser", password="pass12345")
        Service.objects.create(name="smart card", organization="org",
                               documents="doc1", steps="step1",
                               keywords="ملی,کارت")
        client = Client()
        client.login(username="searchuser", password="pass12345")
        response = client.get("/search/", {"q": "smart"})
        assert response.status_code == 200
        assert "smart card" in str(response.content)

    def test_search_empty_query_returns_empty(self):
        user = User.objects.create_user("searchuser2", password="pass12345")
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
        user = User.objects.create_user("listuser", password="pass12345")
        Service.objects.create(name="beta", organization="o", documents="d", steps="s")
        Service.objects.create(name="alpha", organization="o", documents="d", steps="s")
        client = Client()
        client.login(username="listuser", password="pass12345")
        response = client.get("/services/")
        assert response.status_code == 200
        content = str(response.content)
        assert content.index("alpha") < content.index("beta")


@pytest.mark.django_db
class TestServiceDetailView:

    def test_requires_login(self):
        client = Client()
        response = client.get("/service/1/")
        assert response.status_code == 302

    def test_shows_service_details(self):
        user = User.objects.create_user("detailuser", password="pass12345")
        service = Service.objects.create(name="passport", organization="police",
                                         documents="doc1", steps="step1")
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
        user = User.objects.create_user("faquser", password="pass12345")
        FAQ.objects.create(question="q1", answer="a1", order=2)
        FAQ.objects.create(question="q2", answer="a2", order=1)
        client = Client()
        client.login(username="faquser", password="pass12345")
        response = client.get("/faq/")
        assert response.status_code == 200
        assert "q1" in str(response.content)


@pytest.mark.django_db
class TestAboutAndContactViews:

    def test_about_requires_login(self):
        client = Client()
        response = client.get("/about/")
        assert response.status_code == 302

    def test_about_renders_when_logged_in(self):
        user = User.objects.create_user("aboutuser", password="pass12345")
        client = Client()
        client.login(username="aboutuser", password="pass12345")
        response = client.get("/about/")
        assert response.status_code == 200

    def test_contact_requires_login(self):
        client = Client()
        response = client.get("/contact/")
        assert response.status_code == 302

    def test_contact_renders_when_logged_in(self):
        user = User.objects.create_user("contactuser", password="pass12345")
        client = Client()
        client.login(username="contactuser", password="pass12345")
        response = client.get("/contact/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestLogoutView:

    def test_logout_redirects_to_login(self):
        user = User.objects.create_user("logoutuser", password="pass12345")
        client = Client()
        client.login(username="logoutuser", password="pass12345")
        response = client.get("/logout/")
        assert response.status_code == 302


@pytest.mark.django_db
class TestNearbyCentersView:

    def test_requires_login(self):
        client = Client()
        response = client.get("/nearby-centers/")
        assert response.status_code == 302

    def test_renders_when_logged_in(self):
        user = User.objects.create_user("nearbyuser", password="pass12345")
        client = Client()
        client.login(username="nearbyuser", password="pass12345")
        response = client.get("/nearby-centers/")
        assert response.status_code == 200
