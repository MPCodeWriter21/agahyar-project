#!/usr/bin/env python
"""Create a compressed backup of the PostgreSQL database.

Usage::

    uv run python scripts/backup_db.py
    uv run python scripts/backup_db.py --output-dir /path/to/backups

Requires ``pg_dump`` to be available on ``$PATH``.
Falls back to Django's ``dumpdata`` when ``pg_dump`` is not installed.
"""

import gzip
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from log21 import ColorizingArgumentParser

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agahyar_project.settings")


def _django_settings():
    """Return the Django DATABASES config dict."""
    import django

    django.setup()
    from django.conf import settings

    return settings.DATABASES["default"]


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def backup_pg_dump(db: dict, output_dir: str) -> str:
    """Use pg_dump to create a gzipped SQL backup. Returns the file path."""
    ts = _timestamp()
    filename = f"backup_{ts}.sql.gz"
    filepath = os.path.join(output_dir, filename)

    env = os.environ.copy()
    if db.get("USER"):
        env["PGUSER"] = db["USER"]
    if db.get("PASSWORD"):
        env["PGPASSWORD"] = db["PASSWORD"]
    if db.get("HOST"):
        env["PGHOST"] = db["HOST"]
    if db.get("PORT"):
        env["PGPORT"] = str(db["PORT"])

    cmd = ["pg_dump", "--no-owner", "--no-privileges", db["NAME"]]

    with open(filepath, "wb") as f:
        proc = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            os.remove(filepath)
            raise RuntimeError(
                f"pg_dump failed (exit {proc.returncode}): "
                f"{proc.stderr.decode(errors='replace')}"
            )

    return filepath


def backup_dumpdata(db: dict, output_dir: str) -> str:
    """Fall back to Django dumpdata. Returns the file path."""
    ts = _timestamp()
    filename = f"backup_{ts}.json.gz"
    filepath = os.path.join(output_dir, filename)

    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "src", "manage.py"),
        "dumpdata",
        "--indent",
        "2",
        "--natural-foreign",
        "--natural-primary",
    ]

    with gzip.open(filepath, "wt", encoding="utf-8") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            os.remove(filepath)
            raise RuntimeError(
                f"dumpdata failed (exit {proc.returncode}): "
                f"{proc.stderr.decode(errors='replace')}"
            )

    return filepath


def main() -> None:
    parser = ColorizingArgumentParser(description="Backup the project database.")
    parser.add_argument(
        "--output-dir",
        default=os.path.join(BASE_DIR, "backups"),
        help="Directory to write backups into (default: ./backups).",
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    db = _django_settings()
    has_pg_dump = shutil.which("pg_dump") is not None

    if has_pg_dump:
        print("Using pg_dump ...")
        filepath = backup_pg_dump(db, output_dir)
    else:
        print("pg_dump not found, falling back to Django dumpdata ...")
        filepath = backup_dumpdata(db, output_dir)

    size_kb = os.path.getsize(filepath) / 1024
    print(f"Backup created: {filepath} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
