"""Migrate existing ServiceCenter.phone data to ServiceCenterPhone records."""

from django.db import migrations


def forward(apps, schema_editor):
    """Move each ServiceCenter.phone value into a ServiceCenterPhone row."""
    ServiceCenter = apps.get_model("services", "ServiceCenter")
    ServiceCenterPhone = apps.get_model("services", "ServiceCenterPhone")

    centers = ServiceCenter.objects.exclude(phone__exact="").exclude(phone__isnull=True)
    phones_to_create = []
    for center in centers:
        phones_to_create.append(
            ServiceCenterPhone(
                center_id=center.id,
                phone=center.phone,
                label="main",
                order=0,
            )
        )
    ServiceCenterPhone.objects.bulk_create(phones_to_create)


def backward(apps, schema_editor):
    """Copy the first phone back to ServiceCenter.phone (best-effort)."""
    ServiceCenter = apps.get_model("services", "ServiceCenter")
    ServiceCenterPhone = apps.get_model("services", "ServiceCenterPhone")

    for center in ServiceCenter.objects.all():
        first = (
            ServiceCenterPhone.objects.filter(center=center)
            .order_by("order", "id")
            .first()
        )
        if first:
            center.phone = first.phone
            center.save(update_fields=["phone"])


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0016_add_servicecenterphone"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
