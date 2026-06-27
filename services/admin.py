from django.contrib import admin

from .models import FAQ, ContactMessage, Service, ServiceCenter, UserProfile


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "cost", "duration")
    search_fields = ("name", "keywords", "organization")
    list_filter = ("organization",)


# ==========================================
# Register UserProfile in admin panel
# ==========================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "phone")
    search_fields = ("user__username", "city")
    list_filter = ("city",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order")
    search_fields = ("question", "answer")
    list_filter = ("category",)


@admin.register(ServiceCenter)
class ServiceCenterAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "city", "phone")
    search_fields = ("name", "address", "city")
    list_filter = ("service", "city")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at")
