import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0009_add_phoneverification"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Comment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField(verbose_name="متن نظر")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش"),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="replies",
                        to="services.comment",
                        verbose_name="نظر والد",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="comments",
                        to="services.service",
                    ),
                ),
                (
                    "service_center",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="comments",
                        to="services.servicecenter",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "نظر",
                "verbose_name_plural": "نظرات",
                "ordering": ["created_at"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("service__isnull", False))
                        | models.Q(("service_center__isnull", False)),
                        name="comment_has_target",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="CenterRating",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "score",
                    models.PositiveSmallIntegerField(verbose_name="امتیاز (۱ تا ۵)"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش"),
                ),
                (
                    "service_center",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ratings",
                        to="services.servicecenter",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="center_ratings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "امتیاز مرکز",
                "verbose_name_plural": "امتیازهای مراکز",
                "ordering": ["-created_at"],
                "unique_together": {("user", "service_center")},
            },
        ),
    ]
