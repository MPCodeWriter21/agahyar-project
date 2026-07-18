"""Root URL configuration for the Agahyar project.

Maps top-level routes (health check, admin panel, services app)
and registers the 429 rate-limit-exceeded handler.
"""

from typing import List

from decouple import config
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import URLPattern, include, path

from agahyar_project import __version__
from services import views as services_views

ADMIN_URL: str = config("ADMIN_URL", default="admin/")


def rate_limit_exceeded(
    request: HttpRequest, exception: Exception = None
) -> HttpResponse:
    """Render a custom 429 page when rate limit is exceeded."""
    return render(request, "429.html", status=429)


handler429 = "agahyar_project.urls.rate_limit_exceeded"


def page_not_found(request: HttpRequest, exception: Exception = None) -> HttpResponse:
    """Render a custom 404 page."""
    return render(request, "404.html", status=404)


handler404 = "agahyar_project.urls.page_not_found"


def server_error(request: HttpRequest) -> HttpResponse:
    """Render a custom 500 page."""
    return render(request, "500.html", status=500)


handler500 = "agahyar_project.urls.server_error"


def health_check(request: HttpRequest) -> HttpResponse:
    """Return version and status for health check probes.

    This is a lightweight endpoint for uptime monitors and load
    balancers.  It checks database connectivity and returns a simple
    status -- no sensitive resource information is exposed.
    """
    from django.db import connection

    health = {"status": "ok", "version": __version__}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health["database"] = "ok"
    except Exception:
        health["status"] = "degraded"
        health["database"] = "error"

    status_code = 200 if health["status"] == "ok" else 503
    return JsonResponse(health, status=status_code)


@staff_member_required
def server_status(request: HttpRequest) -> HttpResponse:
    """Return server resource usage (admin only).

    Exposes CPU, memory, disk, and process information.  Access
    restricted to staff users via the ``@staff_member_required``
    decorator.
    """
    import os

    import psutil
    from django.db import connection

    process = psutil.Process(os.getpid())
    mem = process.memory_info()

    status = {
        "version": __version__,
        "database": "ok",
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_rss_mb": round(mem.rss / (1024 * 1024), 2),
        "memory_percent": round(process.memory_percent(), 2),
        "disk_percent": round(psutil.disk_usage("/").percent, 2),
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        status["database"] = "error"

    if hasattr(process, "num_fds"):
        status["open_fds"] = process.num_fds()

    return JsonResponse(status)


urlpatterns: List[URLPattern] = [
    path("health/", health_check, name="health_check"),
    path("admin/server-status/", server_status, name="server_status"),
    path(
        "admin/stats/",
        services_views.admin_stats,
        name="admin_stats",
    ),
    path(
        "admin/neshan-search/",
        staff_member_required(services_views.neshan_search),
        name="neshan_search",
    ),
    path(ADMIN_URL, admin.site.urls),
    path("api/v1/", include("services.api_urls")),
    path("", include("services.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
