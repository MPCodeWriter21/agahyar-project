"""
ASGI config for agahyar_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import sys

from django.core.asgi import get_asgi_application
from django.core.handlers.asgi import ASGIHandler

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agahyar_project.settings")

application: ASGIHandler = get_asgi_application()
