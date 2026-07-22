"""Data models for the Agahyar services application.

Defines ``Service``, ``UserProfile``, ``FAQ``, ``ServiceCenter``,
``ServiceCenterPhone``, ``ContactMessage``, ``Comment``, ``CenterRating``,
and ``Bookmark`` with Persian verbose names and helper methods.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils import timezone

from services.validators import (
    center_phone_validator,
    iranian_phone_number_validator,
    normalize_phone,
)


class Service(models.Model):
    """Represents a government service offered to citizens."""

    name = models.CharField("نام خدمت", max_length=200, db_index=True)
    organization = models.CharField("سازمان مسئول", max_length=200, db_index=True)
    organization_address = models.CharField(
        "آدرس سازمان", max_length=300, blank=True, null=True
    )
    documents = models.TextField("مدارک مورد نیاز")
    steps = models.TextField("مراحل انجام")
    description = models.TextField("توضیحات", blank=True)
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
        return (
            [d.strip() for d in self.documents.split("|") if d.strip()]
            if self.documents
            else []
        )

    def get_steps_list(self) -> list:
        """Return steps as a list split by ``|``."""
        return (
            [s.strip() for s in self.steps.split("|") if s.strip()]
            if self.steps
            else []
        )

    def get_keywords_list(self) -> list:
        """Return keywords as a list split by ``,``."""
        return (
            [k.strip() for k in self.keywords.split(",") if k.strip()]
            if self.keywords
            else []
        )


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


class PhoneVerification(models.Model):
    """Stores OTP codes for phone number verification during registration."""

    MAX_FAILED_ATTEMPTS = 5

    phone = models.CharField(
        "شماره تماس",
        max_length=11,
        db_index=True,
        validators=[iranian_phone_number_validator],
    )
    otp_code = models.CharField("کد OTP", max_length=128)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    is_used = models.BooleanField("استفاده شده", default=False, db_index=True)
    failed_attempts = models.PositiveSmallIntegerField(
        "تعداد تلاش‌های ناموفق", default=0
    )

    class Meta:
        verbose_name = "احراز هویت شماره"
        verbose_name_plural = "احراز هویت شماره‌ها"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.phone} - {self.created_at}"


class FAQ(models.Model):
    """Frequently Asked Question entry."""

    question = models.CharField("سوال", max_length=300)
    answer = models.TextField("پاسخ")
    category = models.CharField("دسته‌بندی", max_length=100, blank=True)
    order = models.IntegerField("ترتیب نمایش", default=0, db_index=True)

    class Meta:
        verbose_name = "سوال متداول"
        verbose_name_plural = "پرسش‌های متداول"
        ordering = ["order"]

    def __str__(self) -> str:
        return self.question


class ServiceCenter(models.Model):
    """A physical location where government services are provided."""

    services = models.ManyToManyField(
        Service, related_name="service_centers", blank=True, verbose_name="خدمات"
    )
    name = models.CharField("نام مرکز", max_length=200)
    address = models.TextField("آدرس کامل")
    city = models.CharField("شهر", max_length=100, db_index=True)
    description = models.TextField("توضیحات", blank=True, default="")
    working_hours = models.TextField("ساعت کاری", blank=True)
    postal_code = models.CharField("کد پستی", max_length=20, blank=True)
    coordinate = models.PointField(
        "مختصات (عرض,طول)",
        srid=4326,
        null=True,
        blank=True,
        help_text="مختصات جغرافیایی به فرمت 'lat,lng' مثلاً '35.6892,51.3890'",
    )

    class Meta:
        verbose_name = "مرکز ارائه خدمت"
        verbose_name_plural = "مراکز ارائه خدمت"

    def __str__(self) -> str:
        return f"{self.name} - {self.city}"

    def get_map_url(self) -> str:
        """Return a Google Maps URL preferring coordinate over address."""
        if self.coordinate:
            return (
                f"https://www.google.com/maps?q={self.coordinate.y},{self.coordinate.x}"
            )
        return f"https://www.google.com/maps/search/{self.address}"


class ServiceCenterPhone(models.Model):
    """A phone number associated with a service center."""

    LABEL_CHOICES = [
        ("main", "تلفن اصلی"),
        ("fax", "فکس"),
        ("mobile", "موبایل"),
        ("other", "سایر"),
    ]

    center = models.ForeignKey(
        ServiceCenter,
        on_delete=models.CASCADE,
        related_name="phones",
        verbose_name="مرکز",
    )
    phone = models.CharField(
        "شماره تماس",
        max_length=11,
        validators=[center_phone_validator],
    )
    label = models.CharField(
        "برچسب",
        max_length=20,
        choices=LABEL_CHOICES,
        default="main",
    )
    order = models.IntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "شماره تماس مرکز"
        verbose_name_plural = "شماره تماس‌های مراکز"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.get_label_display()}: {self.phone}"

    def clean(self) -> None:
        """Normalise Persian digits to English before validation."""
        self.phone = normalize_phone(self.phone)
        super().clean()

    def full_clean(self, exclude=None, validate_unique=True, **kwargs):
        """Normalise phone digits before field validators run."""
        self.phone = normalize_phone(self.phone)
        super().full_clean(exclude=exclude, validate_unique=validate_unique, **kwargs)

    def save(self, *args, **kwargs):
        """Normalise phone digits before saving."""
        self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)


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


class Comment(models.Model):
    """A user comment on a service or service center, with optional nesting."""

    EDIT_WINDOW_HOURS = 24

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comments",
    )
    service_center = models.ForeignKey(
        "ServiceCenter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="نظر والد",
    )
    text = models.TextField("متن نظر")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)
    edited_at = models.DateTimeField("زمان ویرایش", null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_comments",
        verbose_name="حذف شده توسط",
    )

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(service__isnull=False)
                | models.Q(service_center__isnull=False),
                name="comment_has_target",
            )
        ]

    def __str__(self) -> str:
        target = self.service.name if self.service else self.service_center.name
        return f"{self.user.username} - {target}"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_by_id is not None

    def can_be_edited_by(self, user: User) -> bool:
        if not user.is_authenticated:
            return False
        if self.user_id != user.id:
            return False
        if self.is_deleted:
            return False
        deadline = self.created_at + timedelta(hours=self.EDIT_WINDOW_HOURS)
        return timezone.now() < deadline

    def can_be_deleted_by(self, user: User) -> bool:
        if not user.is_authenticated:
            return False
        if self.is_deleted:
            return False
        return self.user_id == user.id or user.is_staff


class CommentReaction(models.Model):
    """A like (+1) or dislike (-1) on a comment by a user."""

    LIKE = 1
    DISLIKE = -1
    VALUE_CHOICES = [(LIKE, "Like"), (DISLIKE, "Dislike")]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_reactions"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="reactions"
    )
    value = models.SmallIntegerField("امتیاز", choices=VALUE_CHOICES)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "واکنش نظر"
        verbose_name_plural = "واکنش‌های نظرات"
        unique_together = ("user", "comment")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        label = "لایک" if self.value == self.LIKE == 1 else "دیس‌لایک"
        return f"{self.user.username} - {label} - Comment#{self.comment_id}"


class CenterRating(models.Model):
    """A user star rating for a service center."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="center_ratings"
    )
    service_center = models.ForeignKey(
        ServiceCenter, on_delete=models.CASCADE, related_name="ratings"
    )
    score = models.PositiveSmallIntegerField("امتیاز (۱ تا ۵)")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "امتیاز مرکز"
        verbose_name_plural = "امتیازهای مراکز"
        unique_together = ("user", "service_center")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.service_center.name} - {self.score}"


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


class InfoReport(models.Model):
    """A user-submitted report about incorrect or outdated information."""

    class ReportTarget(models.TextChoices):
        SERVICE = "service", "خدمت"
        CENTER = "center", "مرکز"

    class ReportReason(models.TextChoices):
        INCORRECT_INFO = "incorrect_info", "اطلاعات نادرست"
        OUTDATED_INFO = "outdated_info", "اطلاعات قدیمی"
        CLOSED_CENTER = "closed_center", "مرکز تعطیل شده"
        WRONG_ADDRESS = "wrong_address", "آدرس اشتباه"
        WRONG_PHONE = "wrong_phone", "شماره تلفن اشتباه"
        OTHER = "other", "سایر"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="info_reports"
    )
    target_type = models.CharField(
        "نوع مورد", max_length=10, choices=ReportTarget.choices
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name="خدمت",
    )
    service_center = models.ForeignKey(
        ServiceCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name="مرکز",
    )
    reason = models.CharField("دلیل گزارش", max_length=20, choices=ReportReason.choices)
    description = models.TextField("توضیحات", blank=True, default="")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True, db_index=True)
    is_resolved = models.BooleanField("بررسی شده", default=False, db_index=True)
    resolved_at = models.DateTimeField("تاریخ بررسی", null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_reports",
        verbose_name="بررسی شده توسط",
    )
    admin_notes = models.TextField("یادداشت مدیر", blank=True, default="")

    class Meta:
        verbose_name = "گزارش اطلاعات"
        verbose_name_plural = "گزارش‌های اطلاعات"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(target_type="service", service__isnull=False)
                | models.Q(target_type="center", service_center__isnull=False),
                name="report_has_target",
            )
        ]

    def __str__(self) -> str:
        target = self.service if self.service else self.service_center
        return f"{self.user.username} - {target}"
