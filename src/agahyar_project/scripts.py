import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agahyar_project.settings")


def create_superuser() -> None:
    """Run ``createsuperuser`` management command."""
    from django.core.management import execute_from_command_line

    execute_from_command_line([sys.argv[0], "createsuperuser"])
