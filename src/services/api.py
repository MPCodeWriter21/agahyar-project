"""REST API views for the Agahyar services application.

Provides read-only endpoints for services, centers, FAQs, and comments.
Write endpoints for bookmarks and ratings require authentication.
All inputs are aggressively validated; 500 errors from user input
must never reach the client.
"""

from django.db import IntegrityError
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from drf_spectacular.views import SpectacularSwaggerView
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    CommentReaction,
    Service,
    ServiceCenter,
)
from .serializers import (
    BookmarkSerializer,
    CenterRatingSerializer,
    CommentSerializer,
    FAQSerializer,
    MyRatingSerializer,
    ServiceCenterSerializer,
    ServiceSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Grant write access only to the object owner (``obj.user``)."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for government services.

    Supports search by name, organization, and keywords.
    """

    queryset = Service.objects.all().order_by("name")
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "organization", "keywords"]
    ordering_fields = ["name", "organization"]

    def get_queryset(self):
        qs = super().get_queryset()
        org = self.request.query_params.get("organization")
        if org:
            qs = qs.filter(organization__icontains=org)
        return qs.annotate(centers_count=Count("service_centers"))


class ServiceCenterViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for service centers.

    Supports filtering by city and service, search by name and address.
    """

    queryset = (
        ServiceCenter.objects.prefetch_related("services")
        .annotate(avg_rating=Avg("ratings__score"))
        .order_by("name")
    )
    serializer_class = ServiceCenterSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "address", "city"]
    ordering_fields = ["name", "city", "avg_rating"]

    def get_queryset(self):
        qs = super().get_queryset()
        city = self.request.query_params.get("city")
        if city:
            qs = qs.filter(city__icontains=city)
        service_id = self.request.query_params.get("service")
        if service_id:
            qs = qs.filter(services__id=service_id)
        return qs


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for frequently asked questions."""

    queryset = FAQ.objects.all().order_by("order")
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ["question", "answer", "category"]


class CommentViewSet(viewsets.ModelViewSet):
    """API for comments.

    * **List / Retrieve**: public (any user).
    * **Create**: authenticated users only.
    * **Update**: only the comment author, within 24h, not deleted.
    * **Delete**: only the comment author or staff (soft-delete).

    Validation:
    - Exactly one of ``service`` or ``service_center`` must be set.
    - If ``parent`` is given, it must belong to the same target and
      be a top-level comment, and not be deleted.
    - ``text`` must be non-empty and at most 2000 characters.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        if self.action == "destroy":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        qs = (
            Comment.objects.filter(parent__isnull=True)
            .select_related("user", "deleted_by")
            .prefetch_related(
                "replies__user",
                "replies__deleted_by",
                "reactions",
                "replies__reactions",
            )
        )
        service_id = self.request.query_params.get("service")
        center_id = self.request.query_params.get("service_center")
        if service_id and center_id:
            raise ValidationError(
                "فقط یکی از پارامترهای service یا service_center مجاز است."
            )
        if service_id:
            try:
                int(service_id)
            except (ValueError, TypeError):
                raise ValidationError("پارامتر service باید عدد باشد.")
            qs = qs.filter(service_id=service_id)
        if center_id:
            try:
                int(center_id)
            except (ValueError, TypeError):
                raise ValidationError("پارامتر service_center باید عدد باشد.")
            qs = qs.filter(service_center_id=center_id)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.is_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        if comment.user_id != request.user.id and not request.user.is_staff:
            return Response(
                {"detail": "شما مجوز حذف این نظر را ندارید."},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment.deleted_by = request.user
        comment.save(update_fields=["deleted_by", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def react(self, request: Request, pk: int | None = None) -> Response:
        """Toggle a like/dislike reaction on a comment.

        POST ``/api/v1/comments/{id}/react/`` with ``{"value": 1}`` for like
        or ``{"value": -1}`` for dislike.  Sending the same value again
        removes the reaction (toggle).  Sending the opposite value switches.
        """
        comment = get_object_or_404(Comment, pk=pk)
        if comment.is_deleted:
            return Response(
                {"detail": "امکان واکنش به نظر حذف شده وجود ندارد."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if comment.user == request.user:
            return Response(
                {"detail": "امکان واکنش به نظر خودتان وجود ندارد."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        value = request.data.get("value")
        if value not in (CommentReaction.LIKE, CommentReaction.DISLIKE):
            return Response(
                {
                    "detail": "مقدار واکنش نامعتبر است. مقدار ۱ (لایک) یا -۱ (دیس‌لایک) ارسال کنید."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        reaction, created = CommentReaction.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={"value": value},
        )
        if not created:
            if reaction.value == value:
                reaction.delete()
                user_reaction = None
            else:
                reaction.value = value
                reaction.save(update_fields=["value", "updated_at"])
                user_reaction = value
        else:
            user_reaction = value
        likes = comment.reactions.filter(value=CommentReaction.LIKE).count()
        dislikes = comment.reactions.filter(value=CommentReaction.DISLIKE).count()
        return Response(
            {
                "reacted": user_reaction is not None,
                "value": user_reaction,
                "likes": likes,
                "dislikes": dislikes,
                "user_reaction": user_reaction,
            }
        )


class CenterRatingViewSet(viewsets.ViewSet):
    """Private API for the current user's own ratings.

    Exposes only:
    - ``POST /ratings/`` -- create or update own rating (upsert by center).
    - ``GET /ratings/mine/?service_center=<id>`` -- get own rating.
    - ``DELETE /ratings/<id>/`` -- delete own rating.

    Public list / retrieve are intentionally absent.  Average rating
    per center is available via ``/api/v1/centers/<id>/``.
    """

    permission_classes = [permissions.IsAuthenticated]

    def create(self, request: Request) -> Response:
        center_id = request.data.get("service_center")
        if not center_id:
            return Response(
                {"service_center": "این فیلد الزامی است."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not ServiceCenter.objects.filter(id=center_id).exists():
            return Response(
                {"service_center": "مرکز مورد نظر یافت نشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = CenterRating.objects.filter(
            user=request.user, service_center_id=center_id
        ).first()
        if existing:
            serializer = CenterRatingSerializer(
                existing, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = CenterRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(user=request.user)
        except IntegrityError:
            existing = CenterRating.objects.filter(
                user=request.user, service_center_id=center_id
            ).first()
            if existing:
                serializer = CenterRatingSerializer(
                    existing, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            raise
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request: Request) -> Response:
        """Return the current user's rating for a given center.

        Query param ``service_center`` is required.
        """
        center_id = request.query_params.get("service_center")
        if not center_id:
            return Response(
                {"service_center": "این فیلد الزامی است."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            rating = CenterRating.objects.get(
                user=request.user, service_center_id=center_id
            )
        except CenterRating.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = MyRatingSerializer(rating)
        return Response(serializer.data)

    def destroy(self, request: Request, pk: int = None) -> Response:
        """Delete only the caller's own rating."""
        try:
            rating = CenterRating.objects.get(pk=pk, user=request.user)
        except CenterRating.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        rating.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookmarkViewSet(viewsets.ModelViewSet):
    """API for user bookmarks.

    Authenticated users can list, create, and delete their bookmarks.
    Creating a duplicate bookmark returns 409 Conflict instead of 500.
    """

    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related("service")

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(
                {"detail": "این خدمت قبلاً نشانک شده است."},
                status=status.HTTP_409_CONFLICT,
            )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SelfHostedSwaggerView(SpectacularSwaggerView):
    """Swagger UI view that serves CSS/JS from self-hosted static files.

    Instead of loading assets from a CDN, this view points to the
    vendored swagger-ui-dist files under ``static/libs/swagger-ui/``.
    See ``scripts/vendor_static.sh`` for the download script.
    """

    @staticmethod
    def _swagger_ui_resource(filename):
        return static(f"libs/swagger-ui/{filename}")

    @staticmethod
    def _swagger_ui_favicon():
        return static("libs/swagger-ui/favicon-32x32.png")
