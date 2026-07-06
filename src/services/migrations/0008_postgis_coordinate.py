from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point
from django.db import migrations


def convert_coordinates(apps, schema_editor):
    ServiceCenter = apps.get_model("services", "ServiceCenter")
    for center in ServiceCenter.objects.all():
        coord = None
        if getattr(center, "coordinate", None):
            try:
                lat, lng = center.coordinate.split(",")
                coord = Point(float(lng), float(lat), srid=4326)
            except (ValueError, TypeError):
                pass
        if (
            coord is None
            and hasattr(center, "latitude")
            and hasattr(center, "longitude")
        ):
            if center.latitude is not None and center.longitude is not None:
                coord = Point(center.longitude, center.latitude, srid=4326)
        center.coordinate_new = coord
        center.save(update_fields=["coordinate_new"])


class Migration(migrations.Migration):
    dependencies = [
        (
            "services",
            "0007_servicecenter_coordinate_servicecenter_postal_code_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="servicecenter",
            name="coordinate_new",
            field=PointField(
                blank=True,
                help_text="مختصات جغرافیایی به فرمت 'lat,lng' مثلاً '35.6892,51.3890'",
                null=True,
                srid=4326,
                verbose_name="مختصات (عرض,طول)",
            ),
        ),
        migrations.RunPython(
            convert_coordinates, reverse_code=migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name="servicecenter",
            name="latitude",
        ),
        migrations.RemoveField(
            model_name="servicecenter",
            name="longitude",
        ),
        migrations.RemoveField(
            model_name="servicecenter",
            name="coordinate",
        ),
        migrations.RenameField(
            model_name="servicecenter",
            old_name="coordinate_new",
            new_name="coordinate",
        ),
    ]
