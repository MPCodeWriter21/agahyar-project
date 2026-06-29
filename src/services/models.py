from django.contrib.auth.models import User
from django.db import models

from services.validators import iranian_phone_number_validator


class Service(models.Model):
    """Represents a government service offered to citizens."""

    name = models.CharField("نام خدمت", max_length=200)
    organization = models.CharField("سازمان مسئول", max_length=200)
    organization_address = models.CharField(
        "آدرس سازمان", max_length=300, blank=True, null=True
    )
    documents = models.TextField("مدارک مورد نیاز (با | جدا شود)")
    steps = models.TextField("مراحل انجام (با | جدا شود)")
    cost = models.CharField("هزینه تقریبی", max_length=100, blank=True)
    duration = models.CharField("مدت زمان", max_length=100, blank=True)
    more_info_url = models.URLField("لینک اطلاعات بیشتر", blank=True, null=True)
    keywords = models.TextField("کلمات کلیدی", blank=True)

    class Meta:
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"

    def __str__(self) -> str:
        return self.name

    def get_documents_list(self) -> list:
        """Return documents as a list split by ``|``."""
        return self.documents.split("|") if self.documents else []

    def get_steps_list(self) -> list:
        """Return steps as a list split by ``|``."""
        return self.steps.split("|") if self.steps else []


class UserProfile(models.Model):
    """Stores extra profile data for each user (city, neighborhood, phone)."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    city = models.CharField("شهر محل سکونت", max_length=100)
    neighborhood = models.CharField("محله", max_length=100, blank=True, null=True)
    phone = models.CharField(
        "شماره تماس",
        max_length=11,
        blank=True,
        validators=[iranian_phone_number_validator],
    )

    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل‌های کاربران"

    def __str__(self) -> str:
        return f"{self.user.username} - {self.city} - {self.neighborhood}"


class FAQ(models.Model):
    """Frequently Asked Question entry."""

    question = models.CharField("سوال", max_length=300)
    answer = models.TextField("پاسخ")
    category = models.CharField("دسته‌بندی", max_length=100, blank=True)
    order = models.IntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "سوال متداول"
        verbose_name_plural = "پرسش‌های متداول"
        ordering = ["order"]

    def __str__(self) -> str:
        return self.question


class ServiceCenter(models.Model):
    """A physical location where a government service is provided."""

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="centers"
    )
    name = models.CharField("نام مرکز", max_length=200)
    address = models.TextField("آدرس کامل")
    city = models.CharField("شهر", max_length=100)
    phone = models.CharField("شماره تماس", max_length=11, blank=True)
    latitude = models.FloatField("عرض جغرافیایی", null=True, blank=True)
    longitude = models.FloatField("طول جغرافیایی", null=True, blank=True)

    class Meta:
        verbose_name = "مرکز ارائه خدمت"
        verbose_name_plural = "مراکز ارائه خدمت"

    def __str__(self) -> str:
        return f"{self.name} - {self.city}"


class ContactMessage(models.Model):
    """User-submitted contact form message."""

    name = models.CharField("نام", max_length=200)
    email = models.EmailField("ایمیل")
    message = models.TextField("پیام")
    created_at = models.DateTimeField("تاریخ", auto_now_add=True)

    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def __str__(self) -> str:
        return f"{self.name} - {self.email}"


class Bookmark(models.Model):
    """A user's bookmark for a favorite service."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="bookmarks"
    )
    created_at = models.DateTimeField("تاریخ", auto_now_add=True)

    class Meta:
        verbose_name = "نشانک"
        verbose_name_plural = "نشانک‌ها"
        unique_together = ("user", "service")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.service.name}"
