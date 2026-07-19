"""Tests for the Agahyar data models.

Covers ``__str__`` representations, helper methods
(``get_documents_list``, ``get_steps_list``, ``get_map_url``),
unique-together constraints, score-range validation, and
comment edit/delete flags.
"""

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.utils import timezone

from services.models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    ContactMessage,
    Service,
    ServiceCenter,
    ServiceCenterPhone,
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
class TestCommentModel:
    def test_str_service(self):
        user = User.objects.create_user("commenter", password="pass12345")
        service = Service.objects.create(
            name="خدمت تست", organization="org", documents="d", steps="s"
        )
        comment = Comment.objects.create(user=user, service=service, text="نظر تست")
        assert "commenter" in str(comment)
        assert "خدمت تست" in str(comment)

    def test_str_center(self):
        user = User.objects.create_user("commenter2", password="pass12345")
        service = Service.objects.create(
            name="خدمت تست2", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز تست", address="آدرس", city="تهران"
        )
        comment = Comment.objects.create(
            user=user, service_center=center, text="نظر مرکز"
        )
        assert "commenter2" in str(comment)
        assert "مرکز تست" in str(comment)

    def test_reply_nesting(self):
        user = User.objects.create_user("replier", password="pass12345")
        service = Service.objects.create(
            name="test", organization="org", documents="d", steps="s"
        )
        parent = Comment.objects.create(user=user, service=service, text="parent")
        reply = Comment.objects.create(
            user=user, service=service, text="reply", parent=parent
        )
        assert reply.parent_id == parent.id
        assert parent.replies.count() == 1

    def test_multiple_comments_allowed(self):
        user = User.objects.create_user("multi", password="pass12345")
        service = Service.objects.create(
            name="test", organization="org", documents="d", steps="s"
        )
        Comment.objects.create(user=user, service=service, text="first")
        Comment.objects.create(user=user, service=service, text="second")
        assert Comment.objects.filter(user=user, service=service).count() == 2

    def test_ordering_newest_first(self):
        user = User.objects.create_user("orduser", password="pass12345")
        service = Service.objects.create(
            name="ordtest", organization="org", documents="d", steps="s"
        )
        c1 = Comment.objects.create(user=user, service=service, text="old")
        c2 = Comment.objects.create(user=user, service=service, text="new")
        comments = list(Comment.objects.filter(service=service))
        assert comments[0].id == c2.id
        assert comments[1].id == c1.id


@pytest.mark.django_db
class TestCenterRatingModel:
    def test_str(self):
        user = User.objects.create_user("crater", password="pass12345")
        service = Service.objects.create(
            name="خدمت تست", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز تست", address="آدرس", city="تهران"
        )
        rating = CenterRating.objects.create(user=user, service_center=center, score=4)
        assert "crater" in str(rating)
        assert "مرکز تست" in str(rating)
        assert "4" in str(rating)

    def test_unique_together(self):
        user = User.objects.create_user("crater2", password="pass12345")
        service = Service.objects.create(
            name="test", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="test center", address="addr", city="Tehran"
        )
        CenterRating.objects.create(user=user, service_center=center, score=3)
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            CenterRating.objects.create(user=user, service_center=center, score=5)

    def test_score_range(self):
        user = User.objects.create_user("crater3", password="pass12345")
        service = Service.objects.create(
            name="test2", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="test center2", address="addr", city="Tehran"
        )
        rating = CenterRating.objects.create(user=user, service_center=center, score=5)
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


@pytest.mark.django_db
class TestCommentEditDelete:
    def _make_comment(self, username="author"):
        user = User.objects.create_user(username, password="pass12345")
        service = Service.objects.create(
            name="test-svc", organization="org", documents="d", steps="s"
        )
        return Comment.objects.create(user=user, service=service, text="original")

    def test_is_deleted_false_by_default(self):
        c = self._make_comment()
        assert c.is_deleted is False
        assert c.deleted_by is None

    def test_is_deleted_true_when_deleted_by_set(self):
        c = self._make_comment()
        admin = User.objects.create_user("admin", password="pass12345", is_staff=True)
        c.deleted_by = admin
        c.save(update_fields=["deleted_by"])
        assert c.is_deleted is True

    def test_edited_at_none_by_default(self):
        c = self._make_comment()
        assert c.edited_at is None

    def test_edited_at_set_on_edit(self):
        c = self._make_comment()
        c.edited_at = timezone.now()
        c.save(update_fields=["edited_at"])
        assert c.edited_at is not None

    def test_can_be_edited_by_owner_within_24h(self):
        c = self._make_comment("owner")
        assert c.can_be_edited_by(c.user) is True

    def test_cannot_be_edited_by_other(self):
        c = self._make_comment("owner")
        other = User.objects.create_user("other", password="pass12345")
        assert c.can_be_edited_by(other) is False

    def test_cannot_be_edited_by_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        c = self._make_comment()
        assert c.can_be_edited_by(AnonymousUser()) is False

    def test_cannot_be_edited_after_24h(self):
        c = self._make_comment()
        from datetime import timedelta

        c.created_at = timezone.now() - timedelta(hours=25)
        c.save(update_fields=["created_at"])
        assert c.can_be_edited_by(c.user) is False

    def test_cannot_be_edited_when_deleted(self):
        c = self._make_comment()
        c.deleted_by = c.user
        c.save(update_fields=["deleted_by"])
        assert c.can_be_edited_by(c.user) is False

    def test_can_be_deleted_by_owner(self):
        c = self._make_comment("owner")
        assert c.can_be_deleted_by(c.user) is True

    def test_can_be_deleted_by_staff(self):
        c = self._make_comment("owner")
        admin = User.objects.create_user("admin", password="pass12345", is_staff=True)
        assert c.can_be_deleted_by(admin) is True

    def test_cannot_be_deleted_by_other(self):
        c = self._make_comment("owner")
        other = User.objects.create_user("other", password="pass12345")
        assert c.can_be_deleted_by(other) is False

    def test_cannot_be_deleted_when_already_deleted(self):
        c = self._make_comment("owner")
        c.deleted_by = c.user
        c.save(update_fields=["deleted_by"])
        assert c.can_be_deleted_by(c.user) is False


@pytest.mark.django_db
class TestServiceCenterPhoneModel:
    def test_str(self):
        service = Service.objects.create(
            name="خدمت", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز", address="آدرس", city="تهران"
        )
        phone = ServiceCenterPhone.objects.create(
            center=center, phone="02112345678", label="main", order=0
        )
        assert "02112345678" in str(phone)
        assert "تلفن اصلی" in str(phone)

    def test_str_fax(self):
        service = Service.objects.create(
            name="خدمت", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز", address="آدرس", city="تهران"
        )
        phone = ServiceCenterPhone.objects.create(
            center=center, phone="02199999999", label="fax", order=1
        )
        assert "فکس" in str(phone)

    def test_label_choices(self):
        assert ServiceCenterPhone.LABEL_CHOICES[0] == ("main", "تلفن اصلی")
        assert ServiceCenterPhone.LABEL_CHOICES[1] == ("fax", "فکس")
        assert ServiceCenterPhone.LABEL_CHOICES[2] == ("mobile", "موبایل")
        assert ServiceCenterPhone.LABEL_CHOICES[3] == ("other", "سایر")

    def test_default_label_is_main(self):
        service = Service.objects.create(
            name="خدمت", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز", address="آدرس", city="تهران"
        )
        phone = ServiceCenterPhone.objects.create(center=center, phone="02112345678")
        assert phone.label == "main"
        assert phone.order == 0

    def test_center_related_name(self):
        service = Service.objects.create(
            name="خدمت", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز", address="آدرس", city="تهران"
        )
        ServiceCenterPhone.objects.create(
            center=center, phone="02111111111", label="main", order=0
        )
        ServiceCenterPhone.objects.create(
            center=center, phone="02122222222", label="fax", order=1
        )
        assert center.phones.count() == 2

    def test_cascade_delete(self):
        service = Service.objects.create(
            name="خدمت", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز", address="آدرس", city="تهران"
        )
        ServiceCenterPhone.objects.create(center=center, phone="02112345678")
        assert ServiceCenterPhone.objects.count() == 1
        center.delete()
        assert ServiceCenterPhone.objects.count() == 0

    def test_ordering(self):
        service = Service.objects.create(
            name="خدمت", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=service, name="مرکز", address="آدرس", city="تهران"
        )
        ServiceCenterPhone.objects.create(
            center=center, phone="02133333333", label="fax", order=2
        )
        ServiceCenterPhone.objects.create(
            center=center, phone="02111111111", label="main", order=0
        )
        phones = list(center.phones.all())
        assert phones[0].phone == "02111111111"
        assert phones[1].phone == "02133333333"


@pytest.mark.django_db
class TestInfoReportModel:
    """Tests for the InfoReport model."""

    def _create_report(self, target_type="service", **kwargs):
        import uuid

        from services.models import InfoReport

        user = kwargs.pop("user", None)
        if user is None:
            user = User.objects.create_user(
                f"reporter_{uuid.uuid4().hex[:8]}", password="pass12345"
            )
        service = kwargs.pop("service", None)
        center = kwargs.pop("center", None)
        if service is None and target_type == "service":
            service = Service.objects.create(
                name="S", organization="O", documents="d", steps="s"
            )
        if center is None and target_type == "center":
            svc = Service.objects.create(
                name="S", organization="O", documents="d", steps="s"
            )
            center = ServiceCenter.objects.create(
                service=svc, name="C", address="A", city="Tehran"
            )
        return InfoReport.objects.create(
            user=user,
            target_type=target_type,
            service=service,
            service_center=center,
            reason=kwargs.get("reason", "incorrect_info"),
            description=kwargs.get("description", ""),
        )

    def test_str_service(self):
        report = self._create_report(target_type="service")
        assert "reporter" in str(report)

    def test_str_center(self):
        report = self._create_report(target_type="center")
        assert "reporter" in str(report)

    def test_default_not_resolved(self):
        report = self._create_report()
        assert report.is_resolved is False

    def test_service_target(self):
        report = self._create_report(target_type="service")
        assert report.service is not None
        assert report.service_center is None

    def test_center_target(self):
        report = self._create_report(target_type="center")
        assert report.service_center is not None
        assert report.service is None

    def test_ordering_newest_first(self):
        user = User.objects.create_user("reporter_order", password="pass12345")
        svc = Service.objects.create(
            name="SO", organization="OO", documents="d", steps="s"
        )
        r1 = self._create_report(reason="incorrect_info", user=user, service=svc)
        r2 = self._create_report(reason="outdated_info", user=user, service=svc)
        from services.models import InfoReport

        reports = list(InfoReport.objects.all())
        assert reports[0].id == r2.id
        assert reports[1].id == r1.id
