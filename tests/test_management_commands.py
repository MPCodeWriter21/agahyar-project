"""Tests for management commands and the backup script.

Covers ``export_data``, ``import_data``, and ``backup_db``.
"""

import gzip
import json
import os

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management import call_command

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


@pytest.fixture
def sample_data():
    """Create sample data for export/import tests."""
    user = User.objects.create_user("testuser", password="testpass123")
    profile = UserProfile.objects.create(
        user=user, city="Tehran", neighborhood="Valiasr", phone="09121234567"
    )
    service = Service.objects.create(
        name="Test Service",
        organization="Test Org",
        documents="doc1|doc2",
        steps="step1|step2",
        cost="Free",
        duration="1 week",
    )
    center = ServiceCenter.objects.create(
        service=service,
        name="Test Center",
        address="123 Test St",
        city="Tehran",
        phone="02112345678",
        coordinate=Point(51.3890, 35.6892, srid=4326),
    )
    faq = FAQ.objects.create(
        question="Test question?",
        answer="Test answer.",
        category="Test",
        order=1,
    )
    comment = Comment.objects.create(user=user, service=service, text="Great!")
    center_rating = CenterRating.objects.create(
        user=user, service_center=center, score=5
    )
    bookmark = Bookmark.objects.create(user=user, service=service)
    message = ContactMessage.objects.create(
        name="Test User", email="test@example.com", message="Hello!"
    )
    return {
        "user": user,
        "profile": profile,
        "service": service,
        "center": center,
        "faq": faq,
        "comment": comment,
        "center_rating": center_rating,
        "bookmark": bookmark,
        "message": message,
    }


@pytest.mark.django_db
class TestExportData:
    def test_export_json_to_stdout(self, sample_data, capsys):
        call_command("export_data", "--format", "json")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 8
        models = {r["_model"] for r in data}
        assert "services.Service" in models
        assert "services.FAQ" in models

    def test_export_json_to_file(self, sample_data, tmp_path):
        out_file = str(tmp_path / "export.json")
        call_command("export_data", "--format", "json", "--output", out_file)
        assert os.path.exists(out_file)
        with open(out_file, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 8

    def test_export_csv_to_file(self, sample_data, tmp_path):
        out_file = str(tmp_path / "export.csv")
        call_command("export_data", "--format", "csv", "--output", out_file)
        assert os.path.exists(out_file)
        with open(out_file, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) > 1
        assert "_model" in lines[0]


@pytest.mark.django_db
class TestImportData:
    def test_import_json(self, sample_data, tmp_path):
        export_file = str(tmp_path / "export.json")
        call_command("export_data", "--format", "json", "--output", export_file)

        Comment.objects.all().delete()
        CenterRating.objects.all().delete()
        Service.objects.all().delete()
        FAQ.objects.all().delete()
        assert Service.objects.count() == 0

        call_command("import_data", export_file)
        assert Service.objects.count() == 1
        assert FAQ.objects.count() == 1

    def test_import_dry_run(self, sample_data, tmp_path, capsys):
        export_file = str(tmp_path / "export.json")
        call_command("export_data", "--format", "json", "--output", export_file)

        Comment.objects.all().delete()
        CenterRating.objects.all().delete()
        Service.objects.all().delete()
        assert Service.objects.count() == 0

        call_command("import_data", export_file, "--dry-run")
        assert Service.objects.count() == 0
        captured = capsys.readouterr()
        assert "Previewed" in captured.out


@pytest.mark.django_db
class TestBackupDb:
    def test_backup_dumpdata_fallback(self, sample_data, tmp_path, monkeypatch):
        """Test backup using dumpdata fallback when pg_dump is unavailable."""
        import subprocess

        monkeypatch.setattr("shutil.which", lambda x: None)

        from scripts import backup_db

        def fake_run(cmd, stdout=None, stderr=None, **kwargs):
            import json as _json

            data = _json.dumps([{"model": "services.service", "pk": 1, "fields": {}}])
            if hasattr(stdout, "write"):
                stdout.write(data)
            else:
                with open(stdout, "w") as f:
                    f.write(data)
            return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")

        monkeypatch.setattr("subprocess.run", fake_run)

        db = {
            "NAME": "test",
            "USER": "",
            "PASSWORD": "",
            "HOST": "",
            "PORT": "",
        }
        filepath = backup_db.backup_dumpdata(db, str(tmp_path))
        assert os.path.exists(filepath)
        assert filepath.endswith(".json.gz")

        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0
