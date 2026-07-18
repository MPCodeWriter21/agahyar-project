from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0011_migrate_rating_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="phoneverification",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.DeleteModel(
            name="Rating",
        ),
    ]
