from django.db import migrations, models

import services.validators


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0008_postgis_coordinate"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhoneVerification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        max_length=11,
                        validators=[services.validators.iranian_phone_number_validator],
                        verbose_name="شماره تماس",
                    ),
                ),
                (
                    "otp_code",
                    models.CharField(max_length=128, verbose_name="کد OTP"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد"),
                ),
                (
                    "is_used",
                    models.BooleanField(default=False, verbose_name="استفاده شده"),
                ),
            ],
            options={
                "verbose_name": "احراز هویت شماره",
                "verbose_name_plural": "احراز هویت شماره‌ها",
                "ordering": ["-created_at"],
            },
        ),
    ]
