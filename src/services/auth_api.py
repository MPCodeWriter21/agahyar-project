"""REST API views for user authentication.

Provides register (2-step with OTP), login (token obtain), and
logout (token delete) endpoints for mobile and programmatic clients.

Registration flow:
1. ``POST /auth/register/`` -- validate fields, send OTP, store
   registration data in cache, return a random ``pending_token``.
2. ``POST /auth/verify-otp/`` -- verify OTP, create user, return
   auth token.

Login flow:
``POST /auth/login/`` -- verify credentials, return auth token.

Logout flow:
``POST /auth/logout/`` -- delete auth token.
"""

import logging
import secrets
from datetime import timedelta

from django.conf import settings as django_settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from .error_codes import get_error_message
from .models import PhoneVerification, UserProfile
from .otp import generate_otp, hash_otp, verify_otp
from .serializers import (
    ChangePhoneRequestSerializer,
    ChangePhoneVerifySerializer,
    ProfileSerializer,
    RegisterSerializer,
    TokenLoginSerializer,
    VerifyOTPSerializer,
)
from .sms import SMSAPIError, get_sms_client

logger = logging.getLogger(__name__)

PENDING_TOKEN_CACHE_PREFIX = "api-register:"  # nosec B105
PHONE_CHANGE_CACHE_PREFIX = "api-phone-change:"
PENDING_TOKEN_MAX_AGE = timedelta(minutes=5)


def _create_pending_token(data: dict) -> str:
    """Store registration data in cache and return a random token key."""
    token = secrets.token_hex(32)
    cache.set(
        f"{PENDING_TOKEN_CACHE_PREFIX}{token}",
        data,
        timeout=int(PENDING_TOKEN_MAX_AGE.total_seconds()),
    )
    return token


def _get_pending_data(token: str) -> dict | None:
    """Retrieve registration data from cache. Returns None if missing/expired."""
    return cache.get(f"{PENDING_TOKEN_CACHE_PREFIX}{token}")


def _delete_pending_token(token: str) -> None:
    """Remove pending registration data from cache."""
    cache.delete(f"{PENDING_TOKEN_CACHE_PREFIX}{token}")


def _mask_phone(phone: str) -> str:
    """Mask a phone number for display: 0912***4567."""
    if len(phone) >= 7:
        return phone[:4] + "***" + phone[-4:]
    if len(phone) >= 4:
        return phone[:2] + "***" + phone[-2:]
    return "***"


def _create_phone_change_token(new_phone: str, user_id: int) -> str:
    """Store pending phone change in cache and return a random token."""
    token = secrets.token_hex(32)
    cache.set(
        f"{PHONE_CHANGE_CACHE_PREFIX}{token}",
        {"new_phone": new_phone, "user_id": user_id},
        timeout=int(PENDING_TOKEN_MAX_AGE.total_seconds()),
    )
    return token


def _get_phone_change_data(token: str) -> dict | None:
    """Retrieve pending phone change data from cache."""
    return cache.get(f"{PHONE_CHANGE_CACHE_PREFIX}{token}")


def _delete_phone_change_token(token: str) -> None:
    """Remove pending phone change data from cache."""
    cache.delete(f"{PHONE_CHANGE_CACHE_PREFIX}{token}")


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def register_view(request: Request) -> Response:
    """Step 1: validate registration fields and send an OTP.

    Accepts ``username``, ``password``, ``first_name``, ``last_name``,
    ``city``, ``neighborhood``, and ``phone``.

    Returns ``200`` with ``{"pending_token": "...", "phone": "0912***4567"}``.
    The ``pending_token`` expires in 5 minutes.
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    phone = data["phone"]
    otp = generate_otp()

    PhoneVerification.objects.create(
        phone=phone,
        otp_code=hash_otp(otp),
    )

    sms_client = get_sms_client()
    try:
        sms_client.send_otp(phone, otp)
    except SMSAPIError:
        logger.exception("Failed to send OTP to %s", _mask_phone(phone))
        return Response(
            {"detail": get_error_message("otp/send-failed")},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    cache_data = dict(data)
    cache_data["password"] = make_password(data["password"])
    pending_token = _create_pending_token(cache_data)

    return Response(
        {
            "pending_token": pending_token,
            "phone": _mask_phone(phone),
            "message": get_error_message("otp/sent"),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def verify_otp_view(request: Request) -> Response:
    """Step 2: verify OTP and create the user account.

    Accepts ``pending_token`` (from step 1) and ``otp_code`` (6 digits).

    Returns ``201`` with ``{"token": "...", "user_id": ..., "username": "..."}``.
    """
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    pending = _get_pending_data(data["pending_token"])
    if pending is None:
        return Response(
            {"detail": get_error_message("otp/no-pending-registration")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    phone = pending["phone"]

    with transaction.atomic():
        verification = (
            PhoneVerification.objects.select_for_update()
            .filter(phone=phone, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not verification:
            return Response(
                {"detail": get_error_message("otp/invalid")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_max_age = timedelta(
            minutes=getattr(django_settings, "OTP_EXPIRE_MINUTES", 5)
        )
        if timezone.now() - verification.created_at > otp_max_age:
            return Response(
                {"detail": get_error_message("otp/expired")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_otp(verification.otp_code, data["otp_code"]):
            return Response(
                {"detail": get_error_message("otp/invalid")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification.is_used = True
        verification.save(update_fields=["is_used"])

        _delete_pending_token(data["pending_token"])

        user = User(
            username=pending["username"],
            first_name=pending["first_name"],
            last_name=pending["last_name"],
        )
        user.password = pending["password"]
        user.save()
        UserProfile.objects.create(
            user=user,
            city=pending["city"],
            neighborhood=pending["neighborhood"],
            phone=phone,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user_id": user.id, "username": user.username},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def login_view(request: Request) -> Response:
    """Authenticate with username and password, return an auth token.

    Accepts ``username`` and ``password``.

    Returns ``200`` with ``{"token": "...", "user_id": ..., "username": "..."}``.
    """
    serializer = TokenLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    user = authenticate(request, username=data["username"], password=data["password"])
    if user is None:
        return Response(
            {"detail": get_error_message("auth/invalid-credentials")},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user_id": user.id, "username": user.username},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request: Request) -> Response:
    """Delete the caller's auth token (logout).

    Returns ``204 No Content`` on success.
    """
    try:
        request.user.auth_token.delete()
    except (Token.DoesNotExist, ValueError):
        pass
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key="user", rate="30/m", method="PATCH", block=True)
def profile_view(request: Request) -> Response:
    """Get or update the authenticated user's profile.

    GET: returns the current profile.
    PATCH: updates ``first_name``, ``last_name``, ``email``,
    ``city``, and ``neighborhood``.  Phone is not editable here;
    use ``/auth/profile/change-phone/`` instead.

    Returns ``200`` with the updated profile.
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "GET":
        profile_data = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email or "",
            "phone": profile.phone,
            "city": profile.city,
            "neighborhood": profile.neighborhood or "",
        }
        serializer = ProfileSerializer(
            profile_data,
            context={"request": request},
        )
        return Response(serializer.data)

    serializer = ProfileSerializer(
        data=request.data,
        partial=True,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user_fields = ["first_name", "last_name"]
    if "email" in data:
        user.email = data["email"]
        user_fields.append("email")
    user.save(update_fields=user_fields)

    profile.city = data.get("city", profile.city)
    if "neighborhood" in data:
        profile.neighborhood = data["neighborhood"]
    profile.save(update_fields=["city", "neighborhood"])

    profile_data = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email or "",
        "phone": profile.phone,
        "city": profile.city,
        "neighborhood": profile.neighborhood or "",
    }
    serializer = ProfileSerializer(
        profile_data,
        context={"request": request},
    )
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key="user", rate="3/m", method="POST", block=True)
def change_phone_request_view(request: Request) -> Response:
    """Step 1 of phone change: validate and send an OTP to the new number.

    Accepts ``new_phone``.  The new phone must be different from the
    current one and not already used by another user.

    Returns ``200`` with ``{"pending_token": "...", "new_phone": "0912***4567"}``.
    """
    serializer = ChangePhoneRequestSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    new_phone = serializer.validated_data["new_phone"]

    otp = generate_otp()
    PhoneVerification.objects.create(
        phone=new_phone,
        otp_code=hash_otp(otp),
    )

    sms_client = get_sms_client()
    try:
        sms_client.send_otp(new_phone, otp)
    except SMSAPIError:
        logger.exception("Failed to send OTP to %s", _mask_phone(new_phone))
        return Response(
            {"detail": get_error_message("otp/send-failed")},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    pending_token = _create_phone_change_token(new_phone, request.user.id)

    return Response(
        {
            "pending_token": pending_token,
            "new_phone": _mask_phone(new_phone),
            "message": get_error_message("otp/sent"),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def change_phone_verify_view(request: Request) -> Response:
    """Step 2 of phone change: verify OTP and update the phone number.

    Accepts ``pending_token`` (from step 1) and ``otp_code`` (6 digits).

    Returns ``200`` with the updated profile.
    """
    serializer = ChangePhoneVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    pending = _get_phone_change_data(data["pending_token"])
    if pending is None:
        return Response(
            {"detail": get_error_message("otp/no-pending-registration")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if pending["user_id"] != request.user.id:
        return Response(
            {"detail": get_error_message("auth/not-authorized")},
            status=status.HTTP_403_FORBIDDEN,
        )

    new_phone = pending["new_phone"]

    with transaction.atomic():
        verification = (
            PhoneVerification.objects.select_for_update()
            .filter(phone=new_phone, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not verification:
            return Response(
                {"detail": get_error_message("otp/invalid")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_max_age = timedelta(
            minutes=getattr(django_settings, "OTP_EXPIRE_MINUTES", 5)
        )
        if timezone.now() - verification.created_at > otp_max_age:
            return Response(
                {"detail": get_error_message("otp/expired")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_otp(verification.otp_code, data["otp_code"]):
            return Response(
                {"detail": get_error_message("otp/invalid")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification.is_used = True
        verification.save(update_fields=["is_used"])

    _delete_phone_change_token(data["pending_token"])

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.phone = new_phone
    profile.save(update_fields=["phone"])

    profile_data = {
        "username": request.user.username,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email or "",
        "phone": profile.phone,
        "city": profile.city,
        "neighborhood": profile.neighborhood or "",
    }
    serializer = ProfileSerializer(
        profile_data,
        context={"request": request},
    )
    return Response(serializer.data)
