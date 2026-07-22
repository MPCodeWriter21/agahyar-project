"""URL configuration for the Agahyar REST API (v1).

Routes all API endpoints under ``/api/v1/`` and wires up the
drf-spectacular OpenAPI schema and Swagger UI.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include, path
from django.utils.decorators import method_decorator
from drf_spectacular.views import SpectacularAPIView
from rest_framework.routers import DefaultRouter

from .api import (
    BookmarkViewSet,
    CenterRatingViewSet,
    CommentViewSet,
    FAQViewSet,
    SelfHostedSwaggerView,
    ServiceCenterViewSet,
    ServiceViewSet,
)
from .auth_api import (
    change_phone_request_view,
    change_phone_verify_view,
    login_view,
    logout_view,
    profile_view,
    register_view,
    verify_otp_view,
)

router = DefaultRouter()
router.register("services", ServiceViewSet, basename="api-service")
router.register("centers", ServiceCenterViewSet, basename="api-center")
router.register("faqs", FAQViewSet, basename="api-faq")
router.register("comments", CommentViewSet, basename="api-comment")
router.register("bookmarks", BookmarkViewSet, basename="api-bookmark")


@method_decorator(staff_member_required, name="dispatch")
class _StaffSchemaView(SpectacularAPIView):
    """OpenAPI schema view restricted to staff."""


@method_decorator(staff_member_required, name="dispatch")
class _StaffDocsView(SelfHostedSwaggerView):
    """Swagger UI view restricted to staff."""


urlpatterns = [
    path("schema/", _StaffSchemaView.as_view(), name="api-schema"),
    path("docs/", _StaffDocsView.as_view(url_name="api-schema"), name="api-docs"),
    path("", include(router.urls)),
    path(
        "ratings/",
        CenterRatingViewSet.as_view({"post": "create"}),
        name="api-rating-create",
    ),
    path(
        "ratings/mine/",
        CenterRatingViewSet.as_view({"get": "mine"}),
        name="api-rating-mine",
    ),
    path(
        "ratings/<int:pk>/",
        CenterRatingViewSet.as_view({"delete": "destroy"}),
        name="api-rating-destroy",
    ),
    path("auth/register/", register_view, name="api-register"),
    path("auth/verify-otp/", verify_otp_view, name="api-register-verify-otp"),
    path("auth/login/", login_view, name="api-login"),
    path("auth/logout/", logout_view, name="api-logout"),
    path("auth/profile/", profile_view, name="api-profile"),
    path(
        "auth/profile/change-phone/",
        change_phone_request_view,
        name="api-profile-change-phone",
    ),
    path(
        "auth/profile/verify-phone/",
        change_phone_verify_view,
        name="api-profile-verify-phone",
    ),
]
