"""OTP generation and verification utilities.

Provides functions to generate, hash, and verify one-time passwords
using Django's password hashing framework (argon2 by default).
"""

import secrets

from django.contrib.auth.hashers import check_password, make_password


def generate_otp() -> str:
    """Return a cryptographically random 6-digit OTP string.

    :returns: A zero-padded 6-digit string, e.g. ``"004823"``.
    """
    return f"{secrets.randbelow(1000000):06}"


def hash_otp(otp: str) -> str:
    """Hash an OTP string using Django's password hashers.

    :param otp: The plain-text OTP.
    :returns: The hashed OTP string.
    """
    return make_password(otp)


def verify_otp(hashed_otp: str, plain_otp: str) -> bool:
    """Verify a plain-text OTP against its hash.

    :param hashed_otp: The stored hashed OTP.
    :param plain_otp: The user-submitted OTP.
    :returns: ``True`` if the OTP matches, ``False`` otherwise.
    """
    return check_password(plain_otp, hashed_otp)
