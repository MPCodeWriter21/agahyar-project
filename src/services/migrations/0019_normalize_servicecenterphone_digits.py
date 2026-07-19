"""Normalise Persian digits to English in ServiceCenterPhone.phone."""

from django.db import migrations

PERSIAN_TO_ENGLISH = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def forward(apps, schema_editor):
    """Translate any Persian digits stored in ServiceCenterPhone.phone."""
    ServiceCenterPhone = apps.get_model("services", "ServiceCenterPhone")
    for phone_obj in ServiceCenterPhone.objects.all():
        normalised = phone_obj.phone.translate(PERSIAN_TO_ENGLISH)
        if normalised != phone_obj.phone:
            phone_obj.phone = normalised
            phone_obj.save(update_fields=["phone"])


def backward(apps, schema_editor):
    """No-op; English digits are the canonical form."""


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0018_remove_servicecenter_phone"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
