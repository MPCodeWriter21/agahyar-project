"""
WSGI config for agahyar_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.handlers.wsgi import WSGIHandler
from django.core.wsgi import get_wsgi_application

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agahyar_project.settings")

application: WSGIHandler = get_wsgi_application()
