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
    InfoReport,
    PhoneVerification,
    Service,
    ServiceCenter,
    ServiceCenterPhone,
    UserProfile,
)

IMPORT_ORDER = [
    Service,
    FAQ,
    UserProfile,
    ContactMessage,
    ServiceCenter,
    ServiceCenterPhone,
    Comment,
    CenterRating,
    Bookmark,
    InfoReport,
    PhoneVerification,
]

MODEL_MAP = {model._meta.label: model for model in IMPORT_ORDER}


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

        model_order = {model._meta.label: i for i, model in enumerate(IMPORT_ORDER)}
        data.sort(key=lambda r: model_order.get(r.get("_model", ""), len(IMPORT_ORDER)))

        created = 0
        updated = 0
        skipped = 0
        m2m_pending = []

        for record in data:
            model_label = record.get("_model")
            if not model_label or model_label not in MODEL_MAP:
                self.stderr.write(f"Unknown model: {model_label}, skipping.")
                skipped += 1
                continue

            model = MODEL_MAP[model_label]
            fields = {k: v for k, v in record.items() if k != "_model"}
            pk = fields.pop("pk", None)

            m2m_fields = {}
            for field in model._meta.get_fields():
                if field.many_to_many and not field.auto_created:
                    attname = field.attname
                    if attname in fields:
                        m2m_fields[attname] = fields.pop(attname)

            if "coordinate" in fields and isinstance(fields["coordinate"], str):
                try:
                    lat, lng = fields["coordinate"].split(",")
                    fields["coordinate"] = Point(float(lng), float(lat), srid=4326)
                except (ValueError, AttributeError):
                    fields["coordinate"] = None

            if dry_run:
                action = "UPDATE" if pk else "CREATE"
                m2m_info = ""
                if m2m_fields:
                    m2m_info = f" (M2M: {', '.join(m2m_fields.keys())})"
                self.stdout.write(f"  [{action}] {model_label} pk={pk}{m2m_info}")
                created += 1
                continue

            try:
                obj, is_new = model.objects.update_or_create(pk=pk, defaults=fields)
                if is_new:
                    created += 1
                else:
                    updated += 1
                if m2m_fields:
                    m2m_pending.append((obj, m2m_fields, model_label))
            except Exception as exc:
                self.stderr.write(f"  [ERROR] {model_label} pk={pk}: {exc}")
                skipped += 1

        for obj, m2m_fields, model_label in m2m_pending:
            for attname, pk_list in m2m_fields.items():
                if not isinstance(pk_list, list):
                    continue
                try:
                    related_field = getattr(obj, attname)
                    related_model = related_field.model
                    valid_pks = related_model.objects.filter(
                        pk__in=pk_list
                    ).values_list("pk", flat=True)
                    related_field.set(valid_pks)
                except Exception as exc:
                    self.stderr.write(
                        f"  [ERROR] M2M {model_label} pk={obj.pk} {attname}: {exc}"
                    )
                    skipped += 1

        verb = "Previewed" if dry_run else "Imported"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb}: {created} created, {updated} updated, {skipped} skipped."
            )
        )
