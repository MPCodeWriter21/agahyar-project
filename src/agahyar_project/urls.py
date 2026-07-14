"""Root URL configuration for the Agahyar project.

Maps top-level routes (health check, admin panel, services app)
and registers the 429 rate-limit-exceeded handler.
"""

from typing import List

from decouple import config
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import URLPattern, include, path

from agahyar_project import __version__

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
    """Return version and status for health check probes."""
    return JsonResponse({"status": "ok", "version": __version__})


urlpatterns: List[URLPattern] = [
    path("health/", health_check, name="health_check"),
    path(ADMIN_URL, admin.site.urls),
    path("", include("services.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
