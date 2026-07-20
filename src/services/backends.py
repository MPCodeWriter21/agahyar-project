"""Custom authentication backends for the Agahyar application.

Provides ``PhoneEmailBackend`` which allows users to log in with their
username, email address, or phone number (from :class:`UserProfile`).
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .models import UserProfile

logger = logging.getLogger(__name__)

User = get_user_model()


class PhoneEmailBackend(ModelBackend):
    """Authenticate using username, email, or phone number.

    Resolution order:
    1. Exact ``username`` match.
    2. ``email`` match (case-insensitive).
    3. ``profile__phone`` match (via :class:`UserProfile`).

    Falls back to ``None`` if no user is found or the password is wrong.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        user = None

        # Try exact username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass

        # Try email
        if user is None:
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                pass

        # Try phone number via UserProfile
        if user is None:
            try:
                profile = UserProfile.objects.select_related("user").get(phone=username)
                user = profile.user
            except UserProfile.DoesNotExist:
                pass

        if user is not None and user.check_password(password):
            logger.info("User '%s' authenticated via PhoneEmailBackend", user.username)
            return user

        return None
