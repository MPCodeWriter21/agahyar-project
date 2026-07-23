"""Template context processors for the Agahyar project."""

from django.conf import settings
from django.http import HttpRequest


def matomo_context(request: HttpRequest) -> dict:
    """Add Matomo analytics settings to the template context.

    Returns MATOMO_URL and MATOMO_SITE_ID from Django settings so that
    the base template can conditionally render the tracking snippet.
    """
    return {
        "MATOMO_URL": getattr(settings, "MATOMO_URL", ""),
        "MATOMO_SITE_ID": getattr(settings, "MATOMO_SITE_ID", ""),
    }
