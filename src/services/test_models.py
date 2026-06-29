import pytest
from django.contrib.auth.models import User

from services.models import FAQ, ContactMessage, Service, ServiceCenter, UserProfile


@pytest.mark.django_db
class TestServiceModel:
    def test_str(self):
        s = Service.objects.create(
            name="خدمت تست",
            organization="سازمان",
            documents="doc1",
            steps="step1",
        )
        assert str(s) == "خدمت تست"

    def test_get_documents_list(self):
        s = Service.objects.create(
            name="test",
            organization="org",
            documents="doc1|doc2|doc3",
            steps="step1",
        )
        assert s.get_documents_list() == ["doc1", "doc2", "doc3"]

    def test_get_documents_list_empty(self):
        s = Service.objects.create(
            name="test", organization="org", documents="", steps="step1"
        )
        assert s.get_documents_list() == []

    def test_get_steps_list(self):
        s = Service.objects.create(
            name="test",
            organization="org",
            documents="doc1",
            steps="step1|step2",
        )
        assert s.get_steps_list() == ["step1", "step2"]

    def test_get_steps_list_empty(self):
        s = Service.objects.create(
            name="test", organization="org", documents="doc1", steps=""
        )
        assert s.get_steps_list() == []


@pytest.mark.django_db
class TestUserProfileModel:
    def test_str(self):
        user = User.objects.create_user(username="testuser", password="pass")
        profile = UserProfile.objects.create(
            user=user, city="تهران", neighborhood="ونک", phone="09121234567"
        )
        assert "testuser" in str(profile)
        assert "تهران" in str(profile)
        assert "ونک" in str(profile)


@pytest.mark.django_db
class TestFAQModel:
    def test_str(self):
        faq = FAQ.objects.create(
            question="سوال تست؟", answer="پاسخ تست", category="عمومی"
        )
        assert str(faq) == "سوال تست؟"


@pytest.mark.django_db
class TestServiceCenterModel:
    def test_str(self):
        service = Service.objects.create(
            name="خدمت تست", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز تست", address="آدرس", city="تهران"
        )
        assert "مرکز تست" in str(center)
        assert "تهران" in str(center)


@pytest.mark.django_db
class TestContactMessageModel:
    def test_str(self):
        msg = ContactMessage.objects.create(
            name="علی", email="ali@test.com", message="پیام تست"
        )
        assert "علی" in str(msg)
        assert "ali@test.com" in str(msg)
