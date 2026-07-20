"""Import/export resource definitions for all Agahyar models."""

from django.contrib.gis.geos import GEOSGeometry
from import_export import fields, resources
from import_export.widgets import Widget

from .models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    ContactMessage,
    InfoReport,
    Service,
    ServiceCenter,
    ServiceCenterPhone,
    UserProfile,
)


class PointWidget(Widget):
    """Convert PointField to/from WKT string for import/export."""

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        return GEOSGeometry(value, srid=4326)

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        return value.wkt if hasattr(value, "wkt") else str(value)


class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service
        import_id_fields = ("id",)
        fields = (
            "id",
            "name",
            "organization",
            "organization_address",
            "documents",
            "steps",
            "cost",
            "duration",
            "more_info_url",
            "keywords",
        )


class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        import_id_fields = ("id",)
        fields = ("id", "user", "city", "neighborhood", "phone")


class FAQResource(resources.ModelResource):
    class Meta:
        model = FAQ
        import_id_fields = ("id",)
        fields = ("id", "question", "answer", "category", "order")


class ServiceCenterResource(resources.ModelResource):
    coordinate = fields.Field(attribute="coordinate", widget=PointWidget())

    class Meta:
        model = ServiceCenter
        import_id_fields = ("id",)
        fields = (
            "id",
            "name",
            "description",
            "address",
            "city",
            "working_hours",
            "postal_code",
            "coordinate",
            "services",
        )
        export_order = (
            "id",
            "name",
            "description",
            "address",
            "city",
            "working_hours",
            "postal_code",
            "coordinate",
            "services",
        )


class ServiceCenterPhoneResource(resources.ModelResource):
    class Meta:
        model = ServiceCenterPhone
        import_id_fields = ("id",)
        fields = ("id", "center", "phone", "label", "order")


class ContactMessageResource(resources.ModelResource):
    class Meta:
        model = ContactMessage
        import_id_fields = ("id",)
        fields = ("id", "name", "email", "message", "created_at")


class CommentResource(resources.ModelResource):
    class Meta:
        model = Comment
        import_id_fields = ("id",)
        fields = (
            "id",
            "user",
            "service",
            "service_center",
            "parent",
            "text",
            "created_at",
            "updated_at",
            "edited_at",
            "deleted_by",
        )


class CenterRatingResource(resources.ModelResource):
    class Meta:
        model = CenterRating
        import_id_fields = ("id",)
        fields = (
            "id",
            "user",
            "service_center",
            "score",
            "created_at",
            "updated_at",
        )


class BookmarkResource(resources.ModelResource):
    class Meta:
        model = Bookmark
        import_id_fields = ("id",)
        fields = ("id", "user", "service", "created_at")


class InfoReportResource(resources.ModelResource):
    class Meta:
        model = InfoReport
        import_id_fields = ("id",)
        fields = (
            "id",
            "user",
            "target_type",
            "service",
            "service_center",
            "reason",
            "description",
            "created_at",
            "is_resolved",
            "resolved_at",
            "resolved_by",
            "admin_notes",
        )
