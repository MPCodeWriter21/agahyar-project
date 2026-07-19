"""Remove the single phone field from ServiceCenter after migration."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0017_migrate_phone_to_servicecenterphone"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="servicecenter",
            name="phone",
        ),
    ]
