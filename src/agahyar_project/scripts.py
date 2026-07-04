import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agahyar_project.settings")


def migrate() -> None:
    """Run ``migrate`` management command."""
    from django.core.management import execute_from_command_line

    execute_from_command_line([sys.argv[0], "migrate"])


def create_superuser() -> None:
    """Run ``createsuperuser`` management command."""
    from django.core.management import execute_from_command_line

    execute_from_command_line([sys.argv[0], "createsuperuser"])


def run_server() -> None:
    """Run ``runserver`` management command."""
    from django.core.management import execute_from_command_line

    execute_from_command_line([sys.argv[0], "runserver"])
