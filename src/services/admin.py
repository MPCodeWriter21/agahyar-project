"""Admin panel configuration for all Agahyar models.

Registers ``Service``, ``UserProfile``, ``FAQ``, ``ServiceCenter``,
``ContactMessage``, ``Rating``, and ``Bookmark`` with appropriate
list displays, search fields, and filters, plus import/export support.
"""

from django.contrib import admin
from django.contrib.gis.db import models
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin

from .forms import ServiceAdminForm
from .models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    CommentReaction,
    ContactMessage,
    InfoReport,
    Service,
    ServiceCenter,
    ServiceCenterPhone,
    UserProfile,
)
from .resources import (
    BookmarkResource,
    CenterRatingResource,
    CommentResource,
    ContactMessageResource,
    FAQResource,
    InfoReportResource,
    ServiceCenterPhoneResource,
    ServiceCenterResource,
    ServiceResource,
    UserProfileResource,
)
from .widgets import LocalOpenLayersWidget


@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin):
    """Admin configuration for the Service model."""

    resource_classes = [ServiceResource]
    form = ServiceAdminForm
    list_display = ("name", "organization", "cost", "duration")
    search_fields = ("name", "keywords", "organization")
    list_filter = ("organization",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "organization",
                    "organization_address",
                    "cost",
                    "duration",
                    "more_info_url",
                )
            },
        ),
        ("مدارک و مراحل", {"fields": ("documents", "steps", "description")}),
        ("کلمات کلیدی", {"fields": ("keywords",)}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    """Admin configuration for the UserProfile model."""

    resource_classes = [UserProfileResource]
    list_display = ("user", "city", "phone")
    search_fields = ("user__username", "city")
    list_filter = ("city",)


@admin.register(FAQ)
class FAQAdmin(ImportExportModelAdmin):
    """Admin configuration for the FAQ model."""

    resource_classes = [FAQResource]
    list_display = ("question", "category", "order")
    search_fields = ("question", "answer")
    list_filter = ("category",)


class ServiceCenterPhoneInline(admin.TabularInline):
    """Inline editor for phone numbers on a ServiceCenter."""

    model = ServiceCenterPhone
    extra = 1
    fields = ("phone", "label", "order")


@admin.register(ServiceCenterPhone)
class ServiceCenterPhoneAdmin(ImportExportModelAdmin):
    """Admin configuration for ServiceCenterPhone with import/export."""

    resource_classes = [ServiceCenterPhoneResource]
    list_display = ("center", "phone", "label", "order")
    search_fields = ("center__name", "phone")
    list_filter = ("label",)


@admin.register(ServiceCenter)
class ServiceCenterAdmin(ImportExportModelAdmin):
    """Admin configuration for the ServiceCenter model."""

    resource_classes = [ServiceCenterResource]
    list_display = (
        "name",
        "get_services",
        "city",
        "postal_code",
        "working_hours",
        "description",
    )
    search_fields = ("name", "address", "city", "postal_code")
    list_filter = ("city",)
    inlines = [ServiceCenterPhoneInline]
    filter_horizontal = ("services",)
    formfield_overrides = {
        models.GeometryField: {"widget": LocalOpenLayersWidget},
    }

    @admin.display(description="خدمات")
    def get_services(self, obj):
        return ", ".join(obj.services.values_list("name", flat=True)) or "-"


@admin.register(ContactMessage)
class ContactMessageAdmin(ImportExportModelAdmin):
    """Admin configuration for the ContactMessage model."""

    resource_classes = [ContactMessageResource]
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at")


@admin.register(Comment)
class CommentAdmin(ImportExportModelAdmin):
    """Admin configuration for the Comment model."""

    resource_classes = [CommentResource]
    list_display = (
        "user",
        "service",
        "service_center",
        "created_at",
        "edited_at",
        "deleted_by",
    )
    search_fields = ("user__username", "text")
    list_filter = ("created_at", "edited_at")


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    """Admin configuration for the CommentReaction model."""

    list_display = ("user", "comment", "value", "created_at")
    search_fields = ("user__username", "comment__text")
    list_filter = ("value", "created_at")


@admin.register(CenterRating)
class CenterRatingAdmin(ImportExportModelAdmin):
    """Admin configuration for the CenterRating model."""

    resource_classes = [CenterRatingResource]
    list_display = ("user", "service_center", "score", "created_at")
    search_fields = ("user__username", "service_center__name")
    list_filter = ("score", "created_at")


@admin.register(Bookmark)
class BookmarkAdmin(ImportExportModelAdmin):
    """Admin configuration for the Bookmark model."""

    resource_classes = [BookmarkResource]
    list_display = ("user", "service", "created_at")
    search_fields = ("user__username", "service__name")
    list_filter = ("created_at",)


@admin.register(InfoReport)
class InfoReportAdmin(ImportExportModelAdmin):
    """Admin configuration for the InfoReport model."""

    resource_classes = [InfoReportResource]
    list_display = (
        "user",
        "target_type",
        "reason",
        "is_resolved",
        "resolved_by",
        "created_at",
    )
    search_fields = ("user__username", "description", "admin_notes")
    list_filter = ("is_resolved", "target_type", "reason")
    readonly_fields = ("user", "target_type", "service", "service_center", "created_at")
    actions = ["mark_resolved"]

    @admin.action(description="انتخاب شده‌ها را بررسی شده علامت بزن")
    def mark_resolved(self, request, queryset):
        count = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user,
        )
        self.message_user(request, f"{count} گزارش بررسی شد.")
