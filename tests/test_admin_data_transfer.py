"""Tests for the admin data transfer view.

Covers export with model selection, import with dry-run,
and full import with M2M resolution.
"""

import json

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from services.models import FAQ, Service, ServiceCenter, ServiceCenterPhone


def _staff_client():
    """Create and return a logged-in staff client."""
    User.objects.create_user("dataadmin", password="pass12345", is_staff=True)
    client = Client()
    client.login(username="dataadmin", password="pass12345")
    return client


@pytest.mark.django_db
class TestDataTransferPage:
    def test_requires_staff(self):
        client = Client()
        response = client.get("/admin/data-transfer/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_non_staff_gets_403(self):
        User.objects.create_user("regular", password="pass12345")
        client = Client()
        client.login(username="regular", password="pass12345")
        response = client.get("/admin/data-transfer/")
        assert response.status_code in (403, 302)

    def test_staff_gets_200(self):
        client = _staff_client()
        response = client.get("/admin/data-transfer/")
        assert response.status_code == 200

    def test_context_has_model_choices(self):
        client = _staff_client()
        response = client.get("/admin/data-transfer/")
        ctx = response.context
        assert "model_choices" in ctx
        labels = [m["value"] for m in ctx["model_choices"]]
        assert "services.Service" in labels
        assert "services.ServiceCenter" in labels
        assert "services.ServiceCenterPhone" in labels


@pytest.mark.django_db
class TestDataTransferExport:
    def test_export_json_single_model(self):
        Service.objects.create(name="S1", organization="O1", documents="d", steps="s")
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "export", "models": ["services.Service"], "format": "json"},
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        assert "attachment" in response["Content-Disposition"]
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]["_model"] == "services.Service"
        assert data[0]["name"] == "S1"

    def test_export_json_multiple_models(self):
        Service.objects.create(name="S1", organization="O1", documents="d", steps="s")
        FAQ.objects.create(question="Q1", answer="A1", category="general")
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {
                "action": "export",
                "models": ["services.Service", "services.FAQ"],
                "format": "json",
            },
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 2
        models_in_data = {r["_model"] for r in data}
        assert "services.Service" in models_in_data
        assert "services.FAQ" in models_in_data

    def test_export_no_models_returns_error(self):
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "export", "models": [], "format": "json"},
        )
        assert response.status_code == 200
        assert response.context["error"] == "No models selected."

    def test_export_empty_model(self):
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "export", "models": ["services.Service"], "format": "json"},
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data == []

    def test_export_csv(self):
        Service.objects.create(name="S1", organization="O1", documents="d", steps="s")
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "export", "models": ["services.Service"], "format": "csv"},
        )
        assert response.status_code == 200
        assert "text/csv" in response["Content-Type"]
        content = response.content.decode("utf-8")
        assert "S1" in content
        assert "_model" in content


@pytest.mark.django_db
class TestDataTransferImport:
    def test_import_dry_run(self):
        Service.objects.create(
            name="existing", organization="O", documents="d", steps="s"
        )
        payload = json.dumps(
            [
                {
                    "_model": "services.Service",
                    "pk": 999,
                    "name": "imported-service",
                    "organization": "O",
                    "documents": "d",
                    "steps": "s",
                }
            ]
        )
        upload = SimpleUploadedFile(
            "export.json", payload.encode("utf-8"), content_type="application/json"
        )
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "import", "import_file": upload, "dry_run": "on"},
        )
        assert response.status_code == 200
        result = response.context["import_result"]
        assert result["verb"] == "Previewed"
        assert Service.objects.count() == 1
        assert not Service.objects.filter(pk=999).exists()

    def test_import_real(self):
        payload = json.dumps(
            [
                {
                    "_model": "services.Service",
                    "pk": 1001,
                    "name": "imported-svc",
                    "organization": "O",
                    "documents": "d",
                    "steps": "s",
                }
            ]
        )
        upload = SimpleUploadedFile(
            "export.json", payload.encode("utf-8"), content_type="application/json"
        )
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "import", "import_file": upload},
        )
        assert response.status_code == 200
        result = response.context["import_result"]
        assert result["verb"] == "Imported"
        assert result["created"] == 1
        assert Service.objects.filter(pk=1001).exists()

    def test_import_restores_m2m_services(self):
        svc = Service.objects.create(
            name="m2m-svc", organization="O", documents="d", steps="s"
        )
        payload = json.dumps(
            [
                {
                    "_model": "services.ServiceCenter",
                    "pk": 2001,
                    "name": "M2M Center",
                    "address": "addr",
                    "city": "Tehran",
                    "coordinate": "",
                    "services": [svc.pk],
                }
            ]
        )
        upload = SimpleUploadedFile(
            "export.json", payload.encode("utf-8"), content_type="application/json"
        )
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "import", "import_file": upload},
        )
        assert response.status_code == 200
        result = response.context["import_result"]
        assert result["created"] == 1
        center = ServiceCenter.objects.get(pk=2001)
        assert svc in center.services.all()

    def test_import_invalid_json(self):
        upload = SimpleUploadedFile(
            "bad.json", b"not json at all", content_type="application/json"
        )
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "import", "import_file": upload},
        )
        assert response.status_code == 200
        assert "Invalid JSON file" in response.context["error"]

    def test_import_not_array(self):
        payload = json.dumps({"not": "a list"})
        upload = SimpleUploadedFile(
            "export.json", payload.encode("utf-8"), content_type="application/json"
        )
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "import", "import_file": upload},
        )
        assert response.status_code == 200
        assert "Expected a JSON array" in response.context["error"]

    def test_import_no_file(self):
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "import"},
        )
        assert response.status_code == 200
        assert "No file uploaded" in response.context["error"]

    def test_import_fk_ordering(self):
        payload = json.dumps(
            [
                {
                    "_model": "services.ServiceCenter",
                    "pk": 3001,
                    "name": "FK Center",
                    "address": "addr",
                    "city": "Tehran",
                    "coordinate": "",
                    "services": [],
                },
                {
                    "_model": "services.ServiceCenterPhone",
                    "pk": 4001,
                    "center_id": 3001,
                    "phone": "02112345678",
                    "label": "main",
                    "order": 1,
                },
            ]
        )
        upload = SimpleUploadedFile(
            "export.json", payload.encode("utf-8"), content_type="application/json"
        )
        client = _staff_client()
        response = client.post(
            "/admin/data-transfer/",
            {"action": "import", "import_file": upload},
        )
        assert response.status_code == 200
        result = response.context["import_result"]
        assert result["created"] == 2
        assert ServiceCenter.objects.filter(pk=3001).exists()
        assert ServiceCenterPhone.objects.filter(pk=4001).exists()
