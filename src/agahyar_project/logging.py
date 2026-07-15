"""Logging filters and utilities for request tracking."""

import logging
from threading import local

# Shared across middleware and filter -- single instance per process.
_thread_local = local()


class RequestIDFilter(logging.Filter):
    """Inject the current request ID into every log record.

    The middleware stores the request on ``_thread_local.current_request``.
    This filter reads it from there, falling back to ``-`` when no request
    is active (e.g. management commands).
    """

    def filter(self, record):
        request = getattr(_thread_local, "current_request", None)
        record.request_id = getattr(request, "id", "-") if request else "-"
        return True
