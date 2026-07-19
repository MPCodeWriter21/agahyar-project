"""Admin panel configuration for all Agahyar models.

Registers ``Service``, ``UserProfile``, ``FAQ``, ``ServiceCenter``,
``ContactMessage``, ``Rating``, and ``Bookmark`` with appropriate
list displays, search fields, and filters, plus import/export support.
"""

from django.contrib import admin
from django.contrib.gis.db import models
from import_export.admin import ImportExportModelAdmin

from .models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    ContactMessage,
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
    ServiceCenterResource,
    ServiceResource,
    UserProfileResource,
)
from .widgets import LocalOpenLayersWidget


@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin):
    """Admin configuration for the Service model."""

    resource_classes = [ServiceResource]
    list_display = ("name", "organization", "cost", "duration")
    search_fields = ("name", "keywords", "organization")
    list_filter = ("organization",)


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


@admin.register(ServiceCenter)
class ServiceCenterAdmin(ImportExportModelAdmin):
    """Admin configuration for the ServiceCenter model."""

    resource_classes = [ServiceCenterResource]
    list_display = (
        "name",
        "service",
        "city",
        "postal_code",
        "working_hours",
        "description",
    )
    search_fields = ("name", "address", "city", "postal_code")
    list_filter = ("service", "city")
    inlines = [ServiceCenterPhoneInline]
    formfield_overrides = {
        models.GeometryField: {"widget": LocalOpenLayersWidget},
    }


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
