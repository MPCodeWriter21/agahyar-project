from typing import List

from decouple import config
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import URLPattern, include, path

ADMIN_URL: str = config("ADMIN_URL", default="admin/")


def rate_limit_exceeded(
    request: HttpRequest, exception: Exception = None
) -> HttpResponse:
    """Render a custom 429 page when rate limit is exceeded."""
    return render(request, "429.html", status=429)


handler429 = "agahyar_project.urls.rate_limit_exceeded"


def health_check(request: HttpRequest) -> HttpResponse:
    """Return a simple 200 response for health check probes."""
    return HttpResponse("ok")


urlpatterns: List[URLPattern] = [
    path("health/", health_check, name="health_check"),
    path(ADMIN_URL, admin.site.urls),
    path("", include("services.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
