"""DRF serializers for the Agahyar services application."""

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from rest_framework import serializers

from .models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    Service,
    ServiceCenter,
    UserProfile,
)
from .validators import iranian_phone_number_validator


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for :class:`Service` with computed document/step lists."""

    documents_list = serializers.SerializerMethodField()
    steps_list = serializers.SerializerMethodField()
    centers_count = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "organization",
            "organization_address",
            "documents",
            "documents_list",
            "steps",
            "steps_list",
            "cost",
            "duration",
            "more_info_url",
            "keywords",
            "centers_count",
        ]

    def get_documents_list(self, obj: Service) -> list[str]:
        return obj.get_documents_list()

    def get_steps_list(self, obj: Service) -> list[str]:
        return obj.get_steps_list()


class ServiceCenterSerializer(serializers.ModelSerializer):
    """Serializer for :class:`ServiceCenter` with map URL and avg rating."""

    service_name = serializers.CharField(source="service.name", read_only=True)
    map_url = serializers.CharField(read_only=True)
    avg_rating = serializers.FloatField(read_only=True, default=None)

    class Meta:
        model = ServiceCenter
        fields = [
            "id",
            "service",
            "service_name",
            "name",
            "address",
            "city",
            "phone",
            "working_hours",
            "postal_code",
            "map_url",
            "avg_rating",
        ]


class FAQSerializer(serializers.ModelSerializer):
    """Serializer for :class:`FAQ`."""

    class Meta:
        model = FAQ
        fields = ["id", "question", "answer", "category", "order"]


class UserSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested comment display."""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]
        read_only_fields = fields


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for :class:`Comment` with nested user and replies.

    Validates that exactly one target (service or service_center) is set,
    the parent (if given) belongs to the same target, and replies are
    at most one level deep.

    ``service``, ``service_center``, and ``parent`` are immutable after
    creation -- updating them via PATCH/PUT is silently ignored.
    """

    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "service",
            "service_center",
            "parent",
            "text",
            "created_at",
            "updated_at",
            "edited_at",
            "is_deleted",
            "replies",
        ]
        read_only_fields = ["created_at", "updated_at", "edited_at", "is_deleted"]

    def update(self, instance, validated_data):
        for field in ("service", "service_center", "parent"):
            validated_data.pop(field, None)
        if instance.is_deleted:
            raise serializers.ValidationError("امکان ویرایش نظر حذف شده وجود ندارد.")
        if not instance.can_be_edited_by(self.context["request"].user):
            raise serializers.ValidationError(
                "ویرایش نظر فقط تا ۲۴ ساعت پس از ارسال مجاز است."
            )
        if "text" in validated_data and validated_data["text"] != instance.text:
            instance.edited_at = timezone.now()
        return super().update(instance, validated_data)

    def validate_text(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("متن نظر نمی‌تواند خالی باشد.")
        if len(value) > 2000:
            raise serializers.ValidationError("متن نظر بیش از ۲۰۰۰ کاراکتر است.")
        return value

    def validate(self, attrs: dict) -> dict:
        service = attrs.get("service") or getattr(self.instance, "service", None)
        service_center = attrs.get("service_center") or getattr(
            self.instance, "service_center", None
        )
        parent = attrs.get("parent")

        has_service = service is not None
        has_center = service_center is not None

        if not has_service and not has_center:
            raise serializers.ValidationError(
                {"service": "یکی از service یا service_center باید مشخص شود."}
            )
        if has_service and has_center:
            raise serializers.ValidationError(
                {"service": "فقط یکی از service یا service_center مجاز است."}
            )

        if parent is not None:
            if parent.is_deleted:
                raise serializers.ValidationError(
                    {"parent": "امکان پاسخ به نظر حذف شده وجود ندارد."}
                )
            if parent.service != service or parent.service_center != service_center:
                raise serializers.ValidationError(
                    {"parent": "والد متعلق به همان خدمت/مرکز نیست."}
                )
            if parent.parent_id is not None:
                raise serializers.ValidationError(
                    {"parent": "فقط یک سطح پاسخ مجاز است."}
                )

        return attrs

    def get_replies(self, obj: Comment) -> list[dict]:
        if obj.parent_id is not None:
            return []
        return CommentSerializer(
            obj.replies.select_related("user").all(), many=True
        ).data


class CenterRatingSerializer(serializers.ModelSerializer):
    """Serializer for :class:`CenterRating`.

    Used only for creating / updating ratings.  Does not expose the
    user field -- users should never see other users' ratings.
    Validates score is between 1 and 5.
    """

    class Meta:
        model = CenterRating
        fields = [
            "id",
            "service_center",
            "score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_score(self, value: int) -> int:
        if value < 1 or value > 5:
            raise serializers.ValidationError("امتیاز باید بین ۱ تا ۵ باشد.")
        return value


class MyRatingSerializer(serializers.ModelSerializer):
    """Read-only serializer for the current user's own rating.

    Returns only the score for a given service center.  Used by the
    ``GET /api/v1/ratings/mine/`` endpoint.
    """

    class Meta:
        model = CenterRating
        fields = ["id", "service_center", "score", "updated_at"]
        read_only_fields = fields


class BookmarkSerializer(serializers.ModelSerializer):
    """Serializer for :class:`Bookmark`.

    Checks for duplicate bookmarks at the serializer level.
    """

    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source="service", write_only=True
    )

    class Meta:
        model = Bookmark
        fields = ["id", "service", "service_id", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs: dict) -> dict:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            service = attrs.get("service")
            if (
                service
                and Bookmark.objects.filter(user=request.user, service=service).exists()
            ):
                raise serializers.ValidationError("این خدمت قبلاً نشانک شده است.")
        return attrs


class RegisterSerializer(serializers.Serializer):
    """Step-1 serializer for API registration (send OTP).

    Validates all fields and checks uniqueness before the OTP is sent.
    The validated data is signed into a ``pending_token`` for step 2.
    """

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    city = serializers.CharField(max_length=100)
    neighborhood = serializers.CharField(max_length=100)
    phone = serializers.CharField(
        max_length=11,
        validators=[iranian_phone_number_validator],
    )

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("این نام کاربری قبلاً ثبت شده است.")
        return value

    def validate_phone(self, value: str) -> str:
        if UserProfile.objects.filter(phone=value).exists():
            raise serializers.ValidationError("این شماره تماس قبلاً ثبت شده است.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Step-2 serializer for API registration (verify OTP + create account)."""

    pending_token = serializers.CharField()
    otp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        validators=[RegexValidator(r"^\d{6}$", "کد تأیید باید ۶ رقم باشد.")],
    )


class TokenLoginSerializer(serializers.Serializer):
    """Serializer for token-based login via the API."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ProfileSerializer(serializers.Serializer):
    """Serializer for reading and updating user profile.

    ``username`` and ``phone`` are read-only.  Phone changes require
    a separate 2-step OTP flow via ``/auth/profile/change-phone/``.
    """

    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    city = serializers.CharField(max_length=100)
    neighborhood = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    phone = serializers.CharField(read_only=True)

    def validate_email(self, value: str) -> str:
        if value:
            request = self.context.get("request")
            user_id = request.user.id if request else None
            if User.objects.filter(email=value).exclude(id=user_id).exists():
                raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return value


class ChangePhoneRequestSerializer(serializers.Serializer):
    """Step-1 serializer for changing phone number (sends OTP)."""

    new_phone = serializers.CharField(
        max_length=11,
        validators=[iranian_phone_number_validator],
    )

    def validate_new_phone(self, value: str) -> str:
        request = self.context.get("request")
        if request and value == request.user.profile.phone:
            raise serializers.ValidationError(
                "شماره جدید نمی‌تواند همان شماره فعلی باشد."
            )
        if UserProfile.objects.filter(phone=value).exists():
            raise serializers.ValidationError("این شماره تماس قبلاً ثبت شده است.")
        return value


class ChangePhoneVerifySerializer(serializers.Serializer):
    """Step-2 serializer for changing phone number (verify OTP)."""

    pending_token = serializers.CharField()
    otp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        validators=[RegexValidator(r"^\d{6}$", "کد تأیید باید ۶ رقم باشد.")],
    )
