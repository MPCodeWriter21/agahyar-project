"""Tests for import/export resources and admin integration."""

import pytest
import tablib
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client

from services.models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    ContactMessage,
    Service,
    ServiceCenter,
    UserProfile,
)
from services.resources import (
    BookmarkResource,
    CenterRatingResource,
    CommentResource,
    ContactMessageResource,
    FAQResource,
    PointWidget,
    ServiceCenterResource,
    ServiceResource,
    UserProfileResource,
)


class TestPointWidget:
    def test_render_none(self):
        assert PointWidget().render(None) == ""

    def test_render_point(self):
        pt = Point(51.3890, 35.6892, srid=4326)
        result = PointWidget().render(pt)
        assert "POINT" in result

    def test_clean_empty(self):
        assert PointWidget().clean("") is None
        assert PointWidget().clean(None) is None

    def test_clean_valid_wkt(self):
        pt = PointWidget().clean("POINT (51.3890 35.6892)")
        assert pt is not None
        assert pt.x == 51.3890
        assert pt.y == 35.6892
        assert pt.srid == 4326


@pytest.mark.django_db
class TestResourceExport:
    def test_service_resource_export(self):
        Service.objects.create(
            name="export-svc", organization="org", documents="d", steps="s"
        )
        dataset = ServiceResource().export()
        assert len(dataset) == 1
        assert dataset[0][1] == "export-svc"

    def test_service_center_resource_export(self):
        svc = Service.objects.create(
            name="export-center-svc", organization="org", documents="d", steps="s"
        )
        c = ServiceCenter.objects.create(
            name="مرکز صادرات",
            address="آدرس",
            city="تهران",
            coordinate=Point(51.3890, 35.6892, srid=4326),
        )
        c.services.add(svc)
        dataset = ServiceCenterResource().export()
        assert len(dataset) == 1
        assert dataset[0][1] == "مرکز صادرات"

    def test_user_profile_resource_export(self):
        user = User.objects.create_user("export-user")
        UserProfile.objects.create(user=user, city="تهران", phone="09121111111")
        dataset = UserProfileResource().export()
        assert len(dataset) == 1
        assert dataset[0][2] == "تهران"

    def test_faq_resource_export(self):
        FAQ.objects.create(
            question="سوال صادرات؟", answer="پاسخ", category="عمومی", order=1
        )
        dataset = FAQResource().export()
        assert len(dataset) == 1
        assert dataset[0][1] == "سوال صادرات؟"

    def test_contact_message_resource_export(self):
        ContactMessage.objects.create(name="فرستنده", email="a@b.com", message="پیام")
        dataset = ContactMessageResource().export()
        assert len(dataset) == 1
        assert dataset[0][1] == "فرستنده"

    def test_comment_resource_export(self):
        user = User.objects.create_user("comment-export")
        svc = Service.objects.create(
            name="comment-svc", organization="org", documents="d", steps="s"
        )
        Comment.objects.create(user=user, service=svc, text="great service")
        dataset = CommentResource().export()
        assert len(dataset) == 1

    def test_center_rating_resource_export(self):
        user = User.objects.create_user("cr-export")
        svc = Service.objects.create(
            name="cr-svc", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            name="CR Center", address="addr", city="Tehran"
        )
        center.services.add(svc)
        CenterRating.objects.create(user=user, service_center=center, score=4)
        dataset = CenterRatingResource().export()
        assert len(dataset) == 1
        assert str(dataset[0][3]) == "4"

    def test_bookmark_resource_export(self):
        user = User.objects.create_user("bm-export")
        svc = Service.objects.create(
            name="bm-svc", organization="org", documents="d", steps="s"
        )
        Bookmark.objects.create(user=user, service=svc)
        dataset = BookmarkResource().export()
        assert len(dataset) == 1


@pytest.mark.django_db
class TestResourceImport:
    def test_service_resource_import(self):
        dataset = tablib.Dataset(
            headers=["id", "name", "organization", "documents", "steps"],
        )
        dataset.append([1, "imported-svc", "org-imp", "doc1|doc2", "step1"])
        result = ServiceResource().import_data(dataset, dry_run=True)
        assert not result.has_errors()
        assert Service.objects.count() == 0

    def test_service_resource_import_commit(self):
        dataset = tablib.Dataset(
            headers=["id", "name", "organization", "documents", "steps"],
        )
        dataset.append([1, "imported-svc", "org-imp", "doc1|doc2", "step1"])
        ServiceResource().import_data(dataset, dry_run=False)
        assert Service.objects.count() == 1
        svc = Service.objects.get(id=1)
        assert svc.name == "imported-svc"

    def test_service_center_resource_import(self):
        Service.objects.create(
            name="import-target", organization="org", documents="d", steps="s"
        )
        dataset = tablib.Dataset(
            headers=["id", "name", "address", "city", "coordinate"],
        )
        dataset.append(
            [
                1,
                "مرکز وارداتی",
                "آدرس تست",
                "تهران",
                "POINT (51.3890 35.6892)",
            ]
        )
        result = ServiceCenterResource().import_data(dataset, dry_run=False)
        assert not result.has_errors()
        center = ServiceCenter.objects.get(id=1)
        assert center.name == "مرکز وارداتی"
        assert center.coordinate is not None
        assert center.coordinate.x == 51.3890

    def test_user_profile_resource_import(self):
        user = User.objects.create_user("import-user")
        dataset = tablib.Dataset(
            headers=["id", "user", "city", "phone"],
        )
        dataset.append([1, user.id, "اصفهان", "09131111111"])
        UserProfileResource().import_data(dataset, dry_run=False)
        profile = UserProfile.objects.get(id=1)
        assert profile.city == "اصفهان"

    def test_faq_resource_import(self):
        dataset = tablib.Dataset(
            headers=["id", "question", "answer", "category", "order"],
        )
        dataset.append([1, "سوال جدید؟", "پاسخ جدید", "test", 1])
        FAQResource().import_data(dataset, dry_run=False)
        assert FAQ.objects.count() == 1

    def test_comment_resource_import(self):
        user = User.objects.create_user("comment-import")
        svc = Service.objects.create(
            name="import-comment-svc", organization="org", documents="d", steps="s"
        )
        dataset = tablib.Dataset(
            headers=["id", "user", "service", "text"],
        )
        dataset.append([1, user.id, svc.id, "imported comment"])
        CommentResource().import_data(dataset, dry_run=False)
        assert Comment.objects.count() == 1

    def test_center_rating_resource_import(self):
        user = User.objects.create_user("cr-import")
        svc = Service.objects.create(
            name="import-cr-svc", organization="org", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            name="Import Center", address="addr", city="Tehran"
        )
        center.services.add(svc)
        dataset = tablib.Dataset(
            headers=["id", "user", "service_center", "score"],
        )
        dataset.append([1, user.id, center.id, 3])
        CenterRatingResource().import_data(dataset, dry_run=False)
        assert CenterRating.objects.count() == 1
        assert CenterRating.objects.get(id=1).score == 3

    def test_bookmark_resource_import(self):
        user = User.objects.create_user("bm-import")
        svc = Service.objects.create(
            name="import-bm-svc", organization="org", documents="d", steps="s"
        )
        dataset = tablib.Dataset(
            headers=["id", "user", "service"],
        )
        dataset.append([1, user.id, svc.id])
        BookmarkResource().import_data(dataset, dry_run=False)
        assert Bookmark.objects.count() == 1

    def test_contact_message_resource_import(self):
        dataset = tablib.Dataset(
            headers=["id", "name", "email", "message"],
        )
        dataset.append([1, "وارداتی", "imp@test.com", "متن پیام"])
        ContactMessageResource().import_data(dataset, dry_run=False)
        assert ContactMessage.objects.count() == 1


@pytest.mark.django_db
class TestAdminImportExport:
    def test_admin_has_import_button(self):
        User.objects.create_superuser("admin-ie", "a@b.com", "admin12345")
        client = Client()
        assert client.login(username="admin-ie", password="admin12345")
        response = client.get("/admin/services/service/")
        content = response.content.decode()
        assert "import" in content.lower()

    def test_admin_has_export_button(self):
        User.objects.create_superuser("admin-ie2", "a2@b.com", "admin12345")
        client = Client()
        assert client.login(username="admin-ie2", password="admin12345")
        response = client.get("/admin/services/service/")
        content = response.content.decode()
        assert "export" in content.lower()

    def test_admin_import_page_accessible(self):
        User.objects.create_superuser("admin-ie3", "a3@b.com", "admin12345")
        client = Client()
        assert client.login(username="admin-ie3", password="admin12345")
        response = client.get("/admin/services/service/import/")
        assert response.status_code == 200

    def test_admin_export_page_accessible(self):
        User.objects.create_superuser("admin-ie4", "a4@b.com", "admin12345")
        client = Client()
        assert client.login(username="admin-ie4", password="admin12345")
        response = client.get("/admin/services/service/export/")
        assert response.status_code == 200
