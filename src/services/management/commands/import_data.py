"""Import application data from a JSON file produced by export_data.

Usage::

    uv run python manage.py import_data backup.json
    uv run python manage.py import_data backup.json --dry-run
"""

import json

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from services.models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    ContactMessage,
    PhoneVerification,
    Service,
    ServiceCenter,
    UserProfile,
)

MODEL_MAP = {
    model._meta.label: model
    for model in [
        Service,
        ServiceCenter,
        FAQ,
        UserProfile,
        ContactMessage,
        Comment,
        CenterRating,
        Bookmark,
        PhoneVerification,
    ]
}


class Command(BaseCommand):
    """Import application data from a JSON export file."""

    help = "Import application data from a JSON file (produced by export_data)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "filepath",
            help="Path to the JSON export file.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be imported without writing to the database.",
        )

    def handle(self, *args, **options) -> None:
        filepath = options["filepath"]
        dry_run = options["dry_run"]

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        created = 0
        updated = 0
        skipped = 0

        for record in data:
            model_label = record.get("_model")
            if not model_label or model_label not in MODEL_MAP:
                self.stderr.write(f"Unknown model: {model_label}, skipping.")
                skipped += 1
                continue

            model = MODEL_MAP[model_label]
            fields = {k: v for k, v in record.items() if k != "_model"}
            pk = fields.pop("pk", None)

            if "coordinate" in fields and isinstance(fields["coordinate"], str):
                try:
                    lat, lng = fields["coordinate"].split(",")
                    fields["coordinate"] = Point(float(lng), float(lat), srid=4326)
                except (ValueError, AttributeError):
                    fields["coordinate"] = None

            if dry_run:
                action = "UPDATE" if pk else "CREATE"
                self.stdout.write(f"  [{action}] {model_label} pk={pk}")
                created += 1
                continue

            try:
                obj, is_new = model.objects.update_or_create(pk=pk, defaults=fields)
                if is_new:
                    created += 1
                else:
                    updated += 1
            except Exception as exc:
                self.stderr.write(f"  [ERROR] {model_label} pk={pk}: {exc}")
                skipped += 1

        verb = "Previewed" if dry_run else "Imported"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb}: {created} created, {updated} updated, {skipped} skipped."
            )
        )
