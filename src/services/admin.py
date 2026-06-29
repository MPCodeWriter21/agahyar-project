from django.contrib import admin

from .models import (
    FAQ,
    Bookmark,
    ContactMessage,
    Rating,
    Service,
    ServiceCenter,
    UserProfile,
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin configuration for the Service model."""

    list_display = ("name", "organization", "cost", "duration")
    search_fields = ("name", "keywords", "organization")
    list_filter = ("organization",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for the UserProfile model."""

    list_display = ("user", "city", "phone")
    search_fields = ("user__username", "city")
    list_filter = ("city",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin configuration for the FAQ model."""

    list_display = ("question", "category", "order")
    search_fields = ("question", "answer")
    list_filter = ("category",)


@admin.register(ServiceCenter)
class ServiceCenterAdmin(admin.ModelAdmin):
    """Admin configuration for the ServiceCenter model."""

    list_display = ("name", "service", "city", "phone")
    search_fields = ("name", "address", "city")
    list_filter = ("service", "city")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin configuration for the ContactMessage model."""

    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin configuration for the Rating model."""

    list_display = ("user", "service", "score", "created_at")
    search_fields = ("user__username", "service__name", "comment")
    list_filter = ("score", "created_at")


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    """Admin configuration for the Bookmark model."""

    list_display = ("user", "service", "created_at")
    search_fields = ("user__username", "service__name")
    list_filter = ("created_at",)
