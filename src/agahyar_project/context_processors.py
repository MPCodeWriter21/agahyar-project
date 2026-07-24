"""Template context processors for the Agahyar project."""

from django.conf import settings
from django.http import HttpRequest


def matomo_context(request: HttpRequest) -> dict:
    """Add Matomo analytics settings to the template context.

    Returns MATOMO_URL, MATOMO_SITE_ID, and MATOMO_USER_ID from Django
    settings and the current request so that the base template can
    conditionally render the tracking snippet with user identification.
    """
    user_id = ""
    if getattr(request, "user", None) and request.user.is_authenticated:
        user_id = str(request.user.pk)
    return {
        "MATOMO_URL": getattr(settings, "MATOMO_URL", ""),
        "MATOMO_SITE_ID": getattr(settings, "MATOMO_SITE_ID", ""),
        "MATOMO_USER_ID": user_id,
    }
