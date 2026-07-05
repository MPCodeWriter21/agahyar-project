import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from services.models import (
    FAQ,
    Bookmark,
    ContactMessage,
    Rating,
    Service,
    ServiceCenter,
    UserProfile,
)


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

    def test_get_map_url_with_coordinate(self):
        service = Service.objects.create(
            name="خدمت نقشه", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service,
            name="مرکز نقشه",
            address="آدرس",
            city="تهران",
            coordinate=Point(51.389, 35.6892, srid=4326),
        )
        assert "google.com/maps?q=35.6892,51.389" in center.get_map_url()

    def test_get_map_url_without_coordinate(self):
        service = Service.objects.create(
            name="خدمت بدون مختصات", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service,
            name="مرکز بدون مختصات",
            address="تهران، خیابان آزادی",
            city="تهران",
        )
        expected = "https://www.google.com/maps/search/تهران، خیابان آزادی"
        assert center.get_map_url() == expected


@pytest.mark.django_db
class TestContactMessageModel:
    def test_str(self):
        msg = ContactMessage.objects.create(
            name="علی", email="ali@test.com", message="پیام تست"
        )
        assert "علی" in str(msg)
        assert "ali@test.com" in str(msg)


@pytest.mark.django_db
@pytest.mark.django_db
class TestRatingModel:
    def test_str(self):
        user = User.objects.create_user("rater", password="pass12345")
        service = Service.objects.create(
            name="خدمت تست", organization="org", documents="d", steps="s"
        )
        rating = Rating.objects.create(user=user, service=service, score=4)
        assert "rater" in str(rating)
        assert "خدمت تست" in str(rating)
        assert "4" in str(rating)

    def test_unique_together(self):
        user = User.objects.create_user("rater2", password="pass12345")
        service = Service.objects.create(
            name="test", organization="org", documents="d", steps="s"
        )
        Rating.objects.create(user=user, service=service, score=3)
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            Rating.objects.create(user=user, service=service, score=5)

    def test_score_range(self):
        user = User.objects.create_user("rater3", password="pass12345")
        service = Service.objects.create(
            name="test2", organization="org", documents="d", steps="s"
        )
        rating = Rating.objects.create(user=user, service=service, score=5)
        assert 1 <= rating.score <= 5


@pytest.mark.django_db
class TestBookmarkModel:
    def test_str(self):
        user = User.objects.create_user("bookmarkuser", password="pass12345")
        service = Service.objects.create(
            name="خدمت نشانک", organization="org", documents="d", steps="s"
        )
        bookmark = Bookmark.objects.create(user=user, service=service)
        assert "bookmarkuser" in str(bookmark)
        assert "خدمت نشانک" in str(bookmark)

    def test_unique_together(self):
        user = User.objects.create_user("buser", password="pass12345")
        service = Service.objects.create(
            name="test", organization="org", documents="d", steps="s"
        )
        Bookmark.objects.create(user=user, service=service)
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            Bookmark.objects.create(user=user, service=service)
