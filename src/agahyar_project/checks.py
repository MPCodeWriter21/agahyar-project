"""Django system checks for production security configuration."""

from django.conf import settings
from django.core.checks import Error, Warning, register


@register()
def check_secret_key(app_configs, **kwargs):
    """VULN-18: Ensure SECRET_KEY is not the insecure default in production."""
    errors = []
    key = getattr(settings, "SECRET_KEY", "")
    if not settings.DEBUG and key.startswith("django-insecure"):
        errors.append(
            Error(
                "SECRET_KEY must not use the insecure default in production.",
                id="security.E001",
            )
        )
    return errors


_INSECURE_SECURITY_DEFAULTS = {
    "SECURE_SSL_REDIRECT": False,
    "SESSION_COOKIE_SECURE": False,
    "CSRF_COOKIE_SECURE": False,
}


@register()
def check_security_headers(app_configs, **kwargs):
    """VULN-20: Ensure security headers are enabled in production."""
    errors = []
    if settings.DEBUG:
        return errors
    for setting, insecure_value in _INSECURE_SECURITY_DEFAULTS.items():
        actual = getattr(settings, setting, insecure_value)
        if actual == insecure_value:
            errors.append(
                Warning(
                    f"{setting} is {insecure_value!r} in production. "
                    "Enable it to protect against cookie theft and SSL stripping.",
                    id="security.W001",
                )
            )
    hsts = getattr(settings, "SECURE_HSTS_SECONDS", 0)
    if hsts == 0:
        errors.append(
            Warning(
                "SECURE_HSTS_SECONDS is 0 in production. "
                "Set it to a positive value (e.g. 31536000) to enable "
                "HTTP Strict Transport Security.",
                id="security.W002",
            )
        )
    return errors
