"""Migrate existing Rating comments to the Comment model.

Star scores for services are discarded since services no longer have
ratings. Only non-empty comments are preserved.
"""

from django.db import migrations


def forwards(apps, schema_editor):
    Rating = apps.get_model("services", "Rating")
    Comment = apps.get_model("services", "Comment")

    migrated = 0
    for rating in Rating.objects.filter(comment__isnull=False).exclude(comment=""):
        Comment.objects.create(
            user_id=rating.user_id,
            service_id=rating.service_id,
            text=rating.comment,
            created_at=rating.created_at,
            updated_at=rating.updated_at,
        )
        migrated += 1

    print(f"  Migrated {migrated} Rating comments to Comment model.")


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0010_add_comment_and_centerrating"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
