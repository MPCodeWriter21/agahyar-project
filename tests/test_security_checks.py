"""Tests for project-level security checks (VULN-18, VULN-20, VULN-21)."""

from django.core.checks import Error, Warning
from django.test import TestCase, override_settings

from agahyar_project.checks import check_secret_key


class CheckSecretKeyTest(TestCase):
    """VULN-18: SECRET_KEY must not use the insecure default in production."""

    def test_production_with_insecure_key_returns_error(self):
        errors = check_secret_key(
            app_configs=None,
        )
        # Simulate production + insecure key via override_settings
        with override_settings(
            DEBUG=False,
            SECRET_KEY="django-insecure-test-key-for-vuln18",
        ):
            from importlib import reload

            import agahyar_project.checks as mod

            reload(mod)
            errors = mod.check_secret_key(app_configs=None)
        self.assertTrue(any(e.id == "security.E001" for e in errors))
        self.assertTrue(any(isinstance(e, Error) for e in errors))

    def test_production_with_valid_key_returns_no_errors(self):
        with override_settings(
            DEBUG=False,
            SECRET_KEY="a-real-secret-key-not-insecure",
        ):
            from importlib import reload

            import agahyar_project.checks as mod

            reload(mod)
            errors = mod.check_secret_key(app_configs=None)
        self.assertEqual(errors, [])

    def test_debug_mode_with_insecure_key_returns_no_errors(self):
        with override_settings(
            DEBUG=True,
            SECRET_KEY="django-insecure-dev-key",
        ):
            from importlib import reload

            import agahyar_project.checks as mod

            reload(mod)
            errors = mod.check_secret_key(app_configs=None)
        self.assertEqual(errors, [])


class CheckSecurityHeadersTest(TestCase):
    """VULN-20: Security headers must be enabled in production."""

    def test_production_with_headers_disabled_returns_warnings(self):
        with override_settings(
            DEBUG=False,
            SECURE_SSL_REDIRECT=False,
            SESSION_COOKIE_SECURE=False,
            CSRF_COOKIE_SECURE=False,
            SECURE_HSTS_SECONDS=0,
        ):
            from importlib import reload

            import agahyar_project.checks as mod

            reload(mod)
            errors = mod.check_security_headers(app_configs=None)
        self.assertTrue(len(errors) >= 3)
        self.assertTrue(all(isinstance(e, Warning) for e in errors))

    def test_production_with_headers_enabled_returns_no_warnings(self):
        with override_settings(
            DEBUG=False,
            SECURE_SSL_REDIRECT=True,
            SESSION_COOKIE_SECURE=True,
            CSRF_COOKIE_SECURE=True,
            SECURE_HSTS_SECONDS=31536000,
        ):
            from importlib import reload

            import agahyar_project.checks as mod

            reload(mod)
            errors = mod.check_security_headers(app_configs=None)
        self.assertEqual(errors, [])

    def test_debug_mode_skips_header_checks(self):
        with override_settings(
            DEBUG=True,
            SECURE_SSL_REDIRECT=False,
            SESSION_COOKIE_SECURE=False,
            CSRF_COOKIE_SECURE=False,
            SECURE_HSTS_SECONDS=0,
        ):
            from importlib import reload

            import agahyar_project.checks as mod

            reload(mod)
            errors = mod.check_security_headers(app_configs=None)
        self.assertEqual(errors, [])


class ProfilingMiddlewareStaffOnlyTest(TestCase):
    """VULN-21: Profiling report must be visible only to staff users."""

    def setUp(self):
        from django.contrib.auth.models import User

        self.staff_user = User.objects.create_user(
            username="staffuser",
            password="testpass123",
            is_staff=True,
        )
        self.normal_user = User.objects.create_user(
            username="normaluser",
            password="testpass123",
            is_staff=False,
        )

    def _make_request(self, user=None):
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/?profile=1")
        request.user = user or self.normal_user
        return request

    def test_non_staff_does_not_see_profile_report(self):
        from unittest.mock import MagicMock

        from agahyar_project.middleware import ProfilingMiddleware

        middleware = ProfilingMiddleware(lambda r: MagicMock())
        request = self._make_request(self.normal_user)

        # Simulate a profiler result
        request._profiler = MagicMock()
        request._profiler.disable = MagicMock()

        response = MagicMock()
        response.get.return_value = "text/html"
        response.content = b"<html><body></body></html>"

        result = middleware.process_response(request, response)
        # Non-staff should NOT get the profiling block injected
        # (content stays unchanged or doesn't contain profiler-report)
        if hasattr(result, "content"):
            self.assertNotIn(b"profiler-report", result.content)

    def test_staff_sees_profile_report(self):
        from unittest.mock import MagicMock

        from agahyar_project.middleware import ProfilingMiddleware

        middleware = ProfilingMiddleware(lambda r: MagicMock())
        request = self._make_request(self.staff_user)

        request._profiler = MagicMock()
        request._profiler.disable = MagicMock()

        response = MagicMock()
        response.get.return_value = "text/html"
        response.content = b"<html><body></body></html>"

        result = middleware.process_response(request, response)
        if hasattr(result, "content"):
            self.assertIn(b"profiler-report", result.content)

    def test_settings_gates_profiling_on_debug(self):
        """ENABLE_PROFILING should only add middleware when DEBUG=True."""
        from django.conf import settings

        # In test env, DEBUG is typically True, so the middleware should be loaded
        if not settings.DEBUG:
            self.skipTest("DEBUG is False in this test environment")
        self.assertIn(
            "agahyar_project.middleware.ProfilingMiddleware",
            settings.MIDDLEWARE,
        )
