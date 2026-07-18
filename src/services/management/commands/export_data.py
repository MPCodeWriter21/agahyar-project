"""Export application data to JSON or CSV.

Usage::

    uv run python manage.py export_data
    uv run python manage.py export_data --format csv --output data.csv
    uv run python manage.py export_data --output backup.json
"""

import csv
import io
import json
import sys
from datetime import datetime

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

EXPORTABLE_MODELS = [
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


class _JSONEncoder(json.JSONEncoder):
    """Handle datetime and other non-serializable types."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class Command(BaseCommand):
    """Export all application data to JSON or CSV."""

    help = "Export all application data to JSON (default) or CSV."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--format",
            choices=["json", "csv"],
            default="json",
            dest="fmt",
            help="Output format (default: json).",
        )
        parser.add_argument(
            "--output",
            "-o",
            dest="output",
            help="Write to file instead of stdout.",
        )

    def handle(self, *args, **options) -> None:
        fmt = options["fmt"]
        output_path = options.get("output")

        if fmt == "json":
            data = self._collect_json()
            text = __import__("json").dumps(
                data, ensure_ascii=False, indent=2, cls=_JSONEncoder
            )
        else:
            text = self._collect_csv()

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.stdout.write(self.style.SUCCESS(f"Exported to {output_path}"))
        else:
            sys.stdout.write(text)
            sys.stdout.write("\n")

    def _collect_json(self) -> list:
        """Return a list of dicts, one per record with model metadata."""
        result = []
        for model in EXPORTABLE_MODELS:
            label = model._meta.label
            for obj in model.objects.all():
                record = self._model_to_dict(obj)
                record["_model"] = label
                result.append(record)
        self.stderr.write(f"Exported {len(result)} record(s).")
        return result

    def _collect_csv(self) -> str:
        """Return a CSV string with all records."""
        rows = []
        for model in EXPORTABLE_MODELS:
            label = model._meta.label
            for obj in model.objects.all():
                row = self._model_to_dict(obj)
                row["_model"] = label
                rows.append(row)

        if not rows:
            return ""

        all_keys: list[str] = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    all_keys.append(key)
                    seen.add(key)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=all_keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

        self.stderr.write(f"Exported {len(rows)} record(s) to CSV.")
        return buf.getvalue()

    def _model_to_dict(self, obj) -> dict:
        """Convert a model instance to a flat dictionary."""
        data = {}
        for field in obj._meta.get_fields():
            if hasattr(field, "attname"):
                value = getattr(obj, field.attname, None)
                if isinstance(value, Point):
                    value = f"{value.y},{value.x}"
                data[field.attname] = value
        if hasattr(obj, "pk"):
            data["pk"] = obj.pk
        return data
