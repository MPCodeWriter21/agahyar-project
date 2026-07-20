"""Copy service FK data to the new services M2M field."""

from django.db import migrations


def forward(apps, schema_editor):
    ServiceCenter = apps.get_model("services", "ServiceCenter")
    for center in ServiceCenter.objects.select_related("service").all():
        center.services.add(center.service_id)


def backward(apps, schema_editor):
    ServiceCenter = apps.get_model("services", "ServiceCenter")
    for center in ServiceCenter.objects.all():
        first = center.services.first()
        if first:
            center.service_id = first.id
            center.save(update_fields=["service_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0023_add_services_m2m"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
