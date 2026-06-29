from typing import List

from decouple import config
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

urlpatterns: List[URLPattern] = [
    path(ADMIN_URL, admin.site.urls),
    path("", include("services.urls")),
]
