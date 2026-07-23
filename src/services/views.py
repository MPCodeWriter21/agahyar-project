"""View functions for the Agahyar services application.

Covers authentication, dashboard, search, service detail,
bookmarks, ratings, profile, FAQ, contact, nearby centers,
and SEO endpoints, with rate limiting on sensitive views.
"""

import csv
import io
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Q, QuerySet
from django.db.models.functions import TruncWeek
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .error_codes import get_error_message
from .forms import (
    CenterRatingForm,
    CommentForm,
    ContactForm,
    LoginForm,
    OTPVerifyForm,
    PersianPasswordChangeForm,
    PhoneLookupForm,
    ProfileForm,
    RegisterForm,
    SetNewPasswordForm,
    get_default_city,
    get_top_city_choices,
)
from .maps import get_center_locations, get_city_center
from .models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    ContactMessage,
    InfoReport,
    PhoneVerification,
    Service,
    ServiceCenter,
    ServiceCenterPhone,
    UserProfile,
)
from .otp import generate_otp, hash_otp, verify_otp
from .sms import SMSAPIError, get_sms_client
from .suggestion import get_nearest_center

logger = logging.getLogger(__name__)

COMMENTS_PER_PAGE = 5


def save_user_profile(
    user_id: int, city: str, neighborhood: str = "", phone: str = ""
) -> None:
    """Create or update a UserProfile for the given *user_id*.

    :param user_id: Primary key of the User.
    :param city: City name.
    :param neighborhood: Neighborhood name (optional).
    :param phone: Phone number (optional).
    """
    UserProfile.objects.update_or_create(
        user_id=user_id,
        defaults={"city": city, "neighborhood": neighborhood, "phone": phone},
    )


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def register_view(request: HttpRequest) -> HttpResponse:
    """Handle the first step of user registration.

    On POST, validates :class:`RegisterForm`, stores the data in the
    session, generates and sends an OTP to the user's phone, then
    redirects to the verification step.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            request.session["pending_registration"] = form.cleaned_data

            otp = generate_otp()
            PhoneVerification.objects.create(
                phone=phone,
                otp_code=hash_otp(otp),
            )

            sms_client = get_sms_client()
            try:
                sms_client.send_otp(phone, otp)
            except SMSAPIError:
                logger.exception("Failed to send OTP to %s", phone)
                messages.error(request, get_error_message("otp/send-failed"))
                return render(
                    request,
                    "services/auth/register.html",
                    {"form": form, "city_choices": get_top_city_choices()},
                )

            messages.success(request, get_error_message("otp/sent"))
            return redirect("verify_otp")
    else:
        form = RegisterForm()

    return render(
        request,
        "services/auth/register.html",
        {"form": form, "city_choices": get_top_city_choices()},
    )


def _otp_remaining_cooldown(phone: str) -> int:
    """Return the seconds remaining before a new OTP can be sent for *phone*.

    Returns ``0`` if the cooldown has already elapsed or no OTP has been sent
    yet.
    """
    cooldown = getattr(django_settings, "OTP_RESEND_COOLDOWN_SECONDS", 60)
    last_verification = (
        PhoneVerification.objects.filter(phone=phone).order_by("-created_at").first()
    )
    if not last_verification:
        return 0
    elapsed = (timezone.now() - last_verification.created_at).total_seconds()
    return max(0, int(cooldown - elapsed))


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def verify_otp_view(request: HttpRequest) -> HttpResponse:
    """Handle the second step of registration: OTP verification.

    GET: displays the OTP input form.
    POST: verifies the OTP and completes registration if valid.
    """
    if request.user.is_authenticated:
        return redirect("home")

    pending = request.session.get("pending_registration")
    if not pending:
        messages.error(request, get_error_message("otp/no-pending-registration"))
        return redirect("register")

    phone = pending["phone"]
    cooldown = _otp_remaining_cooldown(phone)

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data["otp_code"]
            verification = (
                PhoneVerification.objects.filter(phone=phone, is_used=False)
                .order_by("-created_at")
                .first()
            )

            if not verification:
                messages.error(request, get_error_message("otp/invalid"))
                return render(
                    request,
                    "services/auth/verify_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            if verification.failed_attempts >= PhoneVerification.MAX_FAILED_ATTEMPTS:
                messages.error(request, get_error_message("otp/max-attempts"))
                return render(
                    request,
                    "services/auth/verify_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            otp_max_age = timedelta(
                minutes=getattr(django_settings, "OTP_EXPIRE_MINUTES", 20)
            )
            if timezone.now() - verification.created_at > otp_max_age:
                messages.error(request, get_error_message("otp/expired"))
                return render(
                    request,
                    "services/auth/verify_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            if not verify_otp(verification.otp_code, otp_code):
                verification.failed_attempts += 1
                verification.save(update_fields=["failed_attempts"])
                messages.error(request, get_error_message("otp/invalid"))
                return render(
                    request,
                    "services/auth/verify_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            verification.is_used = True
            verification.save(update_fields=["is_used"])

            user = User.objects.create_user(
                username=pending["username"],
                password=pending["password1"],
                first_name=pending["first_name"],
                last_name=pending["last_name"],
                email=pending.get("email", ""),
            )
            save_user_profile(
                user.id,
                pending["city"],
                pending.get("neighborhood", ""),
                phone,
            )

            del request.session["pending_registration"]
            login(request, user)
            messages.success(
                request,
                get_error_message(
                    "register/welcome",
                    first_name=user.first_name or user.username,
                ),
            )
            return redirect("home")
    else:
        form = OTPVerifyForm()

    return render(
        request,
        "services/auth/verify_otp.html",
        {
            "form": form,
            "phone": phone,
            "cooldown": cooldown,
        },
    )


@ratelimit(key="ip", rate="2/m", method="POST", block=True)
def resend_otp_view(request: HttpRequest) -> HttpResponse:
    """Resend an OTP code for the pending registration.

    Marks all previous OTPs for the phone as used, generates a new one,
    and sends it via SMS.
    """
    if request.user.is_authenticated:
        return redirect("home")

    pending = request.session.get("pending_registration")
    if not pending:
        messages.error(request, get_error_message("otp/no-pending-registration"))
        return redirect("register")

    phone = pending["phone"]

    if request.method == "POST":
        PhoneVerification.objects.filter(phone=phone, is_used=False).update(
            is_used=True
        )

        otp = generate_otp()
        PhoneVerification.objects.create(
            phone=phone,
            otp_code=hash_otp(otp),
        )

        sms_client = get_sms_client()
        try:
            sms_client.send_otp(phone, otp)
        except SMSAPIError:
            logger.exception("Failed to resend OTP to %s", phone)
            messages.error(request, get_error_message("otp/send-failed"))
            return redirect("verify_otp")

        messages.success(request, get_error_message("otp/resend-success"))

    return redirect("verify_otp")


@ratelimit(key="ip", rate="2/m", method="POST", block=True)
def resend_otp_api(request: HttpRequest) -> JsonResponse:
    """API endpoint for resending OTP codes via AJAX.

    POST: validates cooldown, generates a new OTP, sends it, and returns JSON
    with the remaining cooldown for the next resend.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if request.user.is_authenticated:
        return JsonResponse(
            {"error": get_error_message("otp/no-pending-registration")},
            status=400,
        )

    pending = request.session.get("pending_registration")
    if not pending:
        return JsonResponse(
            {"error": get_error_message("otp/no-pending-registration")},
            status=400,
        )

    phone = pending["phone"]
    remaining = _otp_remaining_cooldown(phone)

    if remaining > 0:
        return JsonResponse(
            {
                "error": get_error_message("otp/cooldown", seconds=str(remaining)),
                "cooldown": remaining,
            },
            status=429,
        )

    PhoneVerification.objects.filter(phone=phone, is_used=False).update(is_used=True)

    otp = generate_otp()
    PhoneVerification.objects.create(
        phone=phone,
        otp_code=hash_otp(otp),
    )

    sms_client = get_sms_client()
    try:
        sms_client.send_otp(phone, otp)
    except SMSAPIError:
        logger.exception("Failed to resend OTP to %s", phone)
        return JsonResponse(
            {"error": get_error_message("otp/send-failed")},
            status=500,
        )

    return JsonResponse(
        {
            "message": get_error_message("otp/resend-success"),
            "cooldown": getattr(django_settings, "OTP_RESEND_COOLDOWN_SECONDS", 60),
        },
        status=200,
    )


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def verify_profile_otp_view(request: HttpRequest) -> HttpResponse:
    """Handle OTP verification for a profile phone number change.

    GET: displays the OTP input form.
    POST: verifies the OTP and applies the pending profile update.
    """
    pending = request.session.get("pending_profile_update")
    if not pending:
        messages.error(request, get_error_message("otp/no-pending-profile-update"))
        return redirect("profile")

    phone = pending["phone"]
    cooldown = _otp_remaining_cooldown(phone)

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data["otp_code"]
            verification = (
                PhoneVerification.objects.filter(phone=phone, is_used=False)
                .order_by("-created_at")
                .first()
            )

            if not verification:
                messages.error(request, get_error_message("otp/invalid"))
                return render(
                    request,
                    "services/auth/verify_profile_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            if verification.failed_attempts >= PhoneVerification.MAX_FAILED_ATTEMPTS:
                messages.error(request, get_error_message("otp/max-attempts"))
                return render(
                    request,
                    "services/auth/verify_profile_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            otp_max_age = timedelta(
                minutes=getattr(django_settings, "OTP_EXPIRE_MINUTES", 20)
            )
            if timezone.now() - verification.created_at > otp_max_age:
                messages.error(request, get_error_message("otp/expired"))
                return render(
                    request,
                    "services/auth/verify_profile_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            if not verify_otp(verification.otp_code, otp_code):
                verification.failed_attempts += 1
                verification.save(update_fields=["failed_attempts"])
                messages.error(request, get_error_message("otp/invalid"))
                return render(
                    request,
                    "services/auth/verify_profile_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            verification.is_used = True
            verification.save(update_fields=["is_used"])

            user = request.user
            user.first_name = pending["first_name"]
            user.last_name = pending["last_name"]
            user.email = pending.get("email", "")
            user.save()
            save_user_profile(
                user.id,
                pending["city"],
                pending.get("neighborhood", ""),
                pending["phone"],
            )

            del request.session["pending_profile_update"]
            messages.success(request, get_error_message("profile/updated"))
            return redirect("profile")
    else:
        form = OTPVerifyForm()

    return render(
        request,
        "services/auth/verify_profile_otp.html",
        {"form": form, "phone": phone, "cooldown": cooldown},
    )


@ratelimit(key="ip", rate="2/m", method="POST", block=True)
def resend_profile_otp_api(request: HttpRequest) -> JsonResponse:
    """API endpoint for resending OTP during profile phone change.

    POST: validates cooldown, generates a new OTP, sends it, and returns JSON.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    pending = request.session.get("pending_profile_update")
    if not pending:
        return JsonResponse(
            {"error": get_error_message("otp/no-pending-profile-update")},
            status=400,
        )

    phone = pending["phone"]
    remaining = _otp_remaining_cooldown(phone)

    if remaining > 0:
        return JsonResponse(
            {
                "error": get_error_message("otp/cooldown", seconds=str(remaining)),
                "cooldown": remaining,
            },
            status=429,
        )

    PhoneVerification.objects.filter(phone=phone, is_used=False).update(is_used=True)

    otp = generate_otp()
    PhoneVerification.objects.create(
        phone=phone,
        otp_code=hash_otp(otp),
    )

    sms_client = get_sms_client()
    try:
        sms_client.send_otp(phone, otp)
    except SMSAPIError:
        logger.exception("Failed to resend OTP to %s", phone)
        return JsonResponse(
            {"error": get_error_message("otp/send-failed")},
            status=500,
        )

    return JsonResponse(
        {
            "message": get_error_message("otp/resend-success"),
            "cooldown": getattr(django_settings, "OTP_RESEND_COOLDOWN_SECONDS", 60),
        },
        status=200,
    )


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def login_view(request: HttpRequest) -> HttpResponse:
    """Handle user login.

    Authenticates with :class:`LoginForm`; redirects to home on success.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if form.cleaned_data.get("remember_me"):
                    request.session.set_expiry(2592000)  # 30 days
                else:
                    request.session.set_expiry(0)  # expire on browser close
                messages.success(
                    request,
                    get_error_message(
                        "register/welcome",
                        first_name=user.first_name or user.username,
                    ),
                )
                return redirect("home")
            messages.error(request, get_error_message("auth/invalid-credentials"))
    else:
        form = LoginForm()

    return render(request, "services/auth/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log out the current user and redirect to login."""
    logout(request)
    return redirect("login")


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def password_reset_phone_view(request: HttpRequest) -> HttpResponse:
    """Initiate password reset via phone number.

    GET: display the phone lookup form.
    POST: look up the user by phone, send OTP, redirect to verification.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = PhoneLookupForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            from .models import UserProfile

            profile = (
                UserProfile.objects.select_related("user").filter(phone=phone).first()
            )

            if not profile:
                messages.error(request, get_error_message("auth/no-user-with-phone"))
                return render(
                    request,
                    "services/auth/password_reset_phone_form.html",
                    {"form": form},
                )

            request.session["pending_password_reset"] = {
                "user_id": profile.user_id,
                "phone": phone,
            }

            otp = generate_otp()
            PhoneVerification.objects.create(
                phone=phone,
                otp_code=hash_otp(otp),
            )

            sms_client = get_sms_client()
            try:
                sms_client.send_otp(phone, otp)
            except SMSAPIError:
                logger.exception("Failed to send OTP to %s", phone)
                messages.error(request, get_error_message("otp/send-failed"))
                return render(
                    request,
                    "services/auth/password_reset_phone_form.html",
                    {"form": form},
                )

            messages.success(request, get_error_message("otp/sent"))
            return redirect("verify_password_reset_otp")
    else:
        form = PhoneLookupForm()

    return render(
        request,
        "services/auth/password_reset_phone_form.html",
        {"form": form},
    )


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def verify_password_reset_otp_view(request: HttpRequest) -> HttpResponse:
    """Verify the OTP sent for password reset.

    GET: displays the OTP input form.
    POST: verifies the OTP and redirects to set new password.
    """
    if request.user.is_authenticated:
        return redirect("home")

    pending = request.session.get("pending_password_reset")
    if not pending:
        messages.error(request, get_error_message("otp/no-pending-password-reset"))
        return redirect("password_reset_phone")

    phone = pending["phone"]
    cooldown = _otp_remaining_cooldown(phone)

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data["otp_code"]
            verification = (
                PhoneVerification.objects.filter(phone=phone, is_used=False)
                .order_by("-created_at")
                .first()
            )

            if not verification:
                messages.error(request, get_error_message("otp/invalid"))
                return render(
                    request,
                    "services/auth/verify_password_reset_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            if verification.failed_attempts >= PhoneVerification.MAX_FAILED_ATTEMPTS:
                messages.error(request, get_error_message("otp/max-attempts"))
                return render(
                    request,
                    "services/auth/verify_password_reset_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            otp_max_age = timedelta(
                minutes=getattr(django_settings, "OTP_EXPIRE_MINUTES", 20)
            )
            if timezone.now() - verification.created_at > otp_max_age:
                messages.error(request, get_error_message("otp/expired"))
                return render(
                    request,
                    "services/auth/verify_password_reset_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            if not verify_otp(verification.otp_code, otp_code):
                verification.failed_attempts += 1
                verification.save(update_fields=["failed_attempts"])
                messages.error(request, get_error_message("otp/invalid"))
                return render(
                    request,
                    "services/auth/verify_password_reset_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            verification.is_used = True
            verification.save(update_fields=["is_used"])

            return redirect("set_new_password")
    else:
        form = OTPVerifyForm()

    return render(
        request,
        "services/auth/verify_password_reset_otp.html",
        {"form": form, "phone": phone, "cooldown": cooldown},
    )


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def resend_password_reset_otp_api(request: HttpRequest) -> JsonResponse:
    """API endpoint for resending password-reset OTP codes via AJAX."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if request.user.is_authenticated:
        return JsonResponse(
            {"error": get_error_message("otp/no-pending-password-reset")},
            status=400,
        )

    pending = request.session.get("pending_password_reset")
    if not pending:
        return JsonResponse(
            {"error": get_error_message("otp/no-pending-password-reset")},
            status=400,
        )

    phone = pending["phone"]
    remaining = _otp_remaining_cooldown(phone)

    if remaining > 0:
        return JsonResponse(
            {
                "error": get_error_message("otp/cooldown", seconds=str(remaining)),
                "cooldown": remaining,
            },
            status=429,
        )

    PhoneVerification.objects.filter(phone=phone, is_used=False).update(is_used=True)

    otp = generate_otp()
    PhoneVerification.objects.create(
        phone=phone,
        otp_code=hash_otp(otp),
    )

    sms_client = get_sms_client()
    try:
        sms_client.send_otp(phone, otp)
    except SMSAPIError:
        logger.exception("Failed to resend OTP to %s", phone)
        return JsonResponse(
            {"error": get_error_message("otp/send-failed")},
            status=500,
        )

    return JsonResponse(
        {
            "message": get_error_message("otp/resend-success"),
            "cooldown": getattr(django_settings, "OTP_RESEND_COOLDOWN_SECONDS", 60),
        },
        status=200,
    )


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def set_new_password_view(request: HttpRequest) -> HttpResponse:
    """Set a new password after successful OTP verification for password reset.

    GET: display the new password form.
    POST: validate and set the new password.
    """
    if request.user.is_authenticated:
        return redirect("home")

    pending = request.session.get("pending_password_reset")
    if not pending:
        messages.error(request, get_error_message("otp/no-pending-password-reset"))
        return redirect("password_reset_phone")

    from django.contrib.auth.models import User

    try:
        user = User.objects.get(id=pending["user_id"])
    except User.DoesNotExist:
        messages.error(request, get_error_message("otp/no-pending-password-reset"))
        return redirect("password_reset_phone")

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST, user=user)
        if form.is_valid():
            form.validate_password()
            if not form.errors:
                user.set_password(form.cleaned_data["new_password1"])
                user.save(update_fields=["password"])

                del request.session["pending_password_reset"]
                messages.success(request, get_error_message("password/reset-done"))
                return redirect("login")
    else:
        form = SetNewPasswordForm()

    return render(
        request,
        "services/auth/set_new_password.html",
        {"form": form},
    )


def password_reset_phone_done_view(request: HttpRequest) -> HttpResponse:
    """Display success message after password reset via phone."""
    return render(request, "services/auth/password_reset_phone_done.html")


def home(request: HttpRequest) -> HttpResponse:
    """Render the public home page with popular services and recent FAQs."""
    popular_services: QuerySet = Service.objects.all()[:6]
    faqs: QuerySet = FAQ.objects.all()[:5]
    bookmarked_ids: set[int] = set()
    if request.user.is_authenticated:
        bookmarked_ids = set(
            Bookmark.objects.filter(user=request.user).values_list(
                "service_id", flat=True
            )
        )
    return render(
        request,
        "services/home.html",
        {
            "popular_services": popular_services,
            "faqs": faqs,
            "bookmarked_ids": bookmarked_ids,
        },
    )


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the authenticated user dashboard."""
    popular_services: QuerySet = Service.objects.all()[:6]
    faqs: QuerySet = FAQ.objects.all()[:5]
    bookmarked_ids: set[int] = set(
        Bookmark.objects.filter(user=request.user).values_list("service_id", flat=True)
    )
    return render(
        request,
        "services/dashboard.html",
        {
            "popular_services": popular_services,
            "faqs": faqs,
            "faq_count": FAQ.objects.count(),
            "bookmarked_ids": bookmarked_ids,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "داشبورد"},
            ],
        },
    )


def search(request: HttpRequest) -> HttpResponse:
    """Search services by name, keywords or organization.

    Requires authentication. Results are paginated (12 per page).
    Supports filtering by organization and city.
    """
    if not request.user.is_authenticated:
        return redirect("login")
    query: str = request.GET.get("q", "").strip()[:200]
    org_filter: str = request.GET.get("organization", "").strip()
    city_filter: str = request.GET.get("city", "").strip()

    results: QuerySet = Service.objects.none()
    if query or org_filter or city_filter:
        q = Q()
        if query:
            q &= (
                Q(name__icontains=query)
                | Q(keywords__icontains=query)
                | Q(organization__icontains=query)
            )
        if org_filter:
            q &= Q(organization__icontains=org_filter)
        if city_filter:
            q &= Q(service_centers__city__icontains=city_filter)
        results = Service.objects.filter(q).distinct().order_by("id")

    organizations = (
        Service.objects.values_list("organization", flat=True)
        .distinct()
        .order_by("organization")
    )
    cities = (
        ServiceCenter.objects.values_list("city", flat=True).distinct().order_by("city")
    )

    paginator: Paginator = Paginator(results, 12)
    page_number: str = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    bookmarked_ids: set[int] = set()
    if request.user.is_authenticated:
        bookmarked_ids = set(
            Bookmark.objects.filter(user=request.user).values_list(
                "service_id", flat=True
            )
        )
    return render(
        request,
        "services/search.html",
        {
            "query": query,
            "org_filter": org_filter,
            "city_filter": city_filter,
            "organizations": organizations,
            "cities": cities,
            "page_obj": page_obj,
            "count": paginator.count,
            "bookmarked_ids": bookmarked_ids,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "جستجو"},
            ],
        },
    )


def service_detail(request: HttpRequest, service_id: int) -> HttpResponse:
    """Show details for a single Service.

    Publicly accessible. Attempts to determine the nearest service
    center based on the user's profile city and neighborhood.
    Anonymous users default to Tehran.
    """
    service: Service = get_object_or_404(Service, id=service_id)

    user_city = get_default_city()
    user_neighborhood = ""
    if request.user.is_authenticated:
        try:
            profile: UserProfile = request.user.profile
            user_city = profile.city
            user_neighborhood = profile.neighborhood
        except UserProfile.DoesNotExist:
            pass
    user_city_for_centers = user_city

    nearest_center = get_nearest_center(service.name, user_city, user_neighborhood)

    if not nearest_center:
        nearest_center = ServiceCenter.objects.filter(
            services=service, city__icontains=user_city
        ).first()

    centers_qs = ServiceCenter.objects.filter(services=service).annotate(
        avg_score=Avg("ratings__score")
    )

    coord_center = centers_qs.filter(
        city__icontains=user_city_for_centers, coordinate__isnull=False
    ).first()

    if coord_center:
        from django.contrib.gis.db.models.functions import Distance as DistFunc

        centers_qs = centers_qs.annotate(
            city_distance=DistFunc("coordinate", coord_center.coordinate),
            is_in_city=Count("id", filter=Q(city__icontains=user_city_for_centers)),
        ).order_by(
            "-is_in_city",
            "city_distance",
            F("avg_score").desc(nulls_last=True),
        )
    else:
        centers_qs = centers_qs.annotate(
            is_in_city=Count("id", filter=Q(city__icontains=user_city_for_centers)),
        ).order_by(
            "-is_in_city",
            F("avg_score").desc(nulls_last=True),
        )

    initial_centers = list(centers_qs[:5])
    has_more_centers = centers_qs.count() > 5

    center_locations = get_center_locations(initial_centers)
    city_center = get_city_center(user_city)

    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(
            user=request.user, service=service
        ).exists()

    top_level_comments = (
        Comment.objects.filter(service=service, parent__isnull=True)
        .select_related("user", "deleted_by")
        .prefetch_related(
            "replies__user", "replies__deleted_by", "reactions", "replies__reactions"
        )
    )

    comment_page = int(request.GET.get("comment_page", 1))
    comment_paginator = Paginator(top_level_comments, COMMENTS_PER_PAGE)
    comment_page_obj = comment_paginator.get_page(comment_page)
    has_more_comments = comment_page_obj.has_next()

    from .models import CommentReaction

    comment_reaction_data = {}
    all_comments = list(comment_page_obj) + [
        r for c in comment_page_obj for r in c.replies.all()
    ]
    for c in all_comments:
        likes = 0
        dislikes = 0
        user_rx = None
        user_id = request.user.id if request.user.is_authenticated else None
        for rx in c.reactions.all():
            if rx.value == CommentReaction.LIKE:
                likes += 1
            elif rx.value == CommentReaction.DISLIKE:
                dislikes += 1
            if user_rx is None and user_id and rx.user_id == user_id:
                user_rx = rx.value
        comment_reaction_data[c.id] = (likes, dislikes, user_rx)

    comment_form = None
    if request.user.is_authenticated:
        comment_form = CommentForm()

    return render(
        request,
        "services/service_detail.html",
        {
            "service": service,
            "documents": service.get_documents_list(),
            "steps": service.get_steps_list(),
            "nearest_center": nearest_center,
            "user_city": user_city,
            "user_neighborhood": user_neighborhood,
            "initial_centers": initial_centers,
            "has_more_centers": has_more_centers,
            "center_locations": center_locations,
            "city_center": city_center,
            "is_bookmarked": is_bookmarked,
            "comments": comment_page_obj,
            "has_more_comments": has_more_comments,
            "comment_page": comment_page,
            "comment_form": comment_form,
            "comment_reaction_data": comment_reaction_data,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "خدمات", "url": "/services/"},
                {"label": service.name},
            ],
        },
    )


def services_list(request: HttpRequest) -> HttpResponse:
    """List all services ordered by name, paginated (12 per page)."""
    all_services: QuerySet = Service.objects.all().order_by("name")
    paginator: Paginator = Paginator(all_services, 12)
    page_number: str = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    bookmarked_ids: set[int] = set()
    if request.user.is_authenticated:
        bookmarked_ids = set(
            Bookmark.objects.filter(user=request.user).values_list(
                "service_id", flat=True
            )
        )
    return render(
        request,
        "services/service_list.html",
        {
            "page_obj": page_obj,
            "bookmarked_ids": bookmarked_ids,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "خدمات"},
            ],
        },
    )


def faq_view(request: HttpRequest) -> HttpResponse:
    """Display all FAQs ordered by their ``order`` field."""
    faqs: QuerySet = FAQ.objects.all().order_by("order")
    return render(
        request,
        "services/faq.html",
        {
            "faqs": faqs,
            "faq_count": faqs.count(),
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "سوالات متداول"},
            ],
        },
    )


@login_required
def nearby_centers_view(request: HttpRequest) -> HttpResponse:
    """List nearby service centers grouped by service for the user's city.

    Requires authentication. Falls back to the first available city
    if no profile exists.
    """
    try:
        profile: UserProfile = request.user.profile
        user_city: str = profile.city
        user_neighborhood: str = profile.neighborhood
    except UserProfile.DoesNotExist:
        user_city = get_default_city()
        user_neighborhood = ""

    all_centers = ServiceCenter.objects.filter(
        city__icontains=user_city
    ).prefetch_related("services")

    centers_by_service: dict = {}
    for center in all_centers:
        for svc in center.services.all():
            centers_by_service.setdefault(svc.name, []).append(center)

    for service_name, centers_list in centers_by_service.items():
        nearest = get_nearest_center(service_name, user_city, user_neighborhood)
        for center in centers_list:
            center.is_nearest = nearest is not None and center.id == nearest.id

    return render(
        request,
        "services/nearby_centers.html",
        {
            "centers_by_service": centers_by_service,
            "user_city": user_city,
            "user_neighborhood": user_neighborhood,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "مراکز نزدیک"},
            ],
        },
    )


@staff_member_required
def show_users(request: HttpRequest) -> HttpResponse:
    """List all users with their profile data (staff only)."""
    users: QuerySet = User.objects.select_related("profile").all().order_by("id")
    return render(
        request,
        "services/user_list.html",
        {
            "users": users,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "کاربران"},
            ],
        },
    )


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Show and edit the current user's profile.

    GET: displays the profile data and an edit form.
    POST: saves profile changes (name, email, city, neighborhood, phone) or
          password.
    """
    profile: UserProfile | None = None
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        pass

    profile_initial = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
    }
    if profile:
        profile_initial.update(
            {
                "city": profile.city,
                "neighborhood": profile.neighborhood,
                "phone": profile.phone,
            }
        )

    user_city = profile.city if profile else None

    if request.method == "POST":
        if "update_profile" in request.POST:
            form = ProfileForm(
                request.POST, user_id=request.user.id, user_city=user_city
            )
            password_form = PersianPasswordChangeForm(request.user)
            if form.is_valid():
                new_phone = form.cleaned_data["phone"]
                current_phone = profile.phone if profile else ""
                if new_phone != current_phone:
                    request.session["pending_profile_update"] = form.cleaned_data
                    otp = generate_otp()
                    PhoneVerification.objects.create(
                        phone=new_phone,
                        otp_code=hash_otp(otp),
                    )
                    sms_client = get_sms_client()
                    try:
                        sms_client.send_otp(new_phone, otp)
                    except SMSAPIError:
                        logger.exception("Failed to send OTP to %s", new_phone)
                        del request.session["pending_profile_update"]
                        messages.error(request, get_error_message("otp/send-failed"))
                        return redirect("profile")
                    messages.success(request, get_error_message("otp/sent"))
                    return redirect("verify_profile_otp")
                user = request.user
                user.first_name = form.cleaned_data["first_name"]
                user.last_name = form.cleaned_data["last_name"]
                user.email = form.cleaned_data.get("email", "")
                user.save()
                save_user_profile(
                    request.user.id,
                    form.cleaned_data["city"],
                    form.cleaned_data["neighborhood"],
                    form.cleaned_data["phone"],
                )
                messages.success(request, get_error_message("profile/updated"))
                return redirect("profile")
        elif "change_password" in request.POST:
            form = ProfileForm(initial=profile_initial, user_city=user_city)
            password_form = PersianPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, get_error_message("password/changed"))
                return redirect("profile")
            else:
                messages.error(
                    request, "خطا در تغییر رمز عبور. لطفاً خطوط قرمز را بررسی کنید."
                )
    else:
        form = ProfileForm(initial=profile_initial, user_city=user_city)
        password_form = PersianPasswordChangeForm(request.user)

    city_choices = get_top_city_choices()
    if user_city and not any(v == user_city for v, _ in city_choices[1:]):
        city_choices.insert(1, (user_city, user_city))

    return render(
        request,
        "services/profile.html",
        {
            "form": form,
            "password_form": password_form,
            "profile": profile,
            "city_choices": city_choices,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "پروفایل"},
            ],
        },
    )


def about(request: HttpRequest) -> HttpResponse:
    """Render the about page (public)."""
    return render(
        request,
        "services/about.html",
        {
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "درباره ما"},
            ],
        },
    )


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def contact(request: HttpRequest) -> HttpResponse:
    """Handle the contact form (public).

    On POST, validates :class:`ContactForm` and saves a :class:`ContactMessage`.
    """
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                message=form.cleaned_data["message"],
            )
            messages.success(request, get_error_message("contact/sent"))
            return redirect("contact")
    else:
        form = ContactForm()

    return render(
        request,
        "services/contact.html",
        {
            "form": form,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "تماس با ما"},
            ],
        },
    )


@login_required
def toggle_bookmark(request: HttpRequest, service_id: int) -> HttpResponse:
    """Toggle bookmark on a service.

    GET: redirects to service detail.
    POST (AJAX): toggles bookmark and returns JSON.
    POST (regular): toggles bookmark and redirects to service detail.
    """

    if request.method != "POST":
        return redirect("service_detail", service_id=service_id)

    service = get_object_or_404(Service, id=service_id)
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user, service=service
    )
    if not created:
        bookmark.delete()
        bookmarked = False
        msg = get_error_message("bookmark/removed")
    else:
        bookmarked = True
        msg = get_error_message("bookmark/added")

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        return JsonResponse({"bookmarked": bookmarked, "message": msg})

    messages.success(request, msg)
    return redirect("service_detail", service_id=service_id)


@login_required
def bookmarks_list(request: HttpRequest) -> HttpResponse:
    """List all bookmarked services for the current user."""
    bookmarks = Bookmark.objects.filter(user=request.user).select_related("service")
    return render(
        request,
        "services/bookmarks.html",
        {
            "bookmarks": bookmarks,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "نشانک‌ها"},
            ],
        },
    )


@login_required
def submit_comment(
    request: HttpRequest, service_id: int = 0, center_id: int = 0
) -> HttpResponse:
    """Submit a comment on a service or service center.

    POST only: validates :class:`CommentForm`, creates the comment.
    Supports threaded replies via optional ``parent_id`` field.
    """
    if request.method != "POST":
        if service_id:
            return redirect("service_detail", service_id=service_id)
        return redirect("center_detail", center_id=center_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        parent_id = form.cleaned_data.get("parent_id")
        parent = None
        if parent_id:
            parent = Comment.objects.filter(id=parent_id).first()
            if parent and parent.is_deleted:
                messages.error(
                    request, get_error_message("comment/cannot-reply-deleted")
                )
                if service_id:
                    return redirect("service_detail", service_id=service_id)
                return redirect("center_detail", center_id=center_id)

        comment = Comment(
            user=request.user,
            text=form.cleaned_data["text"],
            parent=parent,
        )
        if service_id:
            comment.service = get_object_or_404(Service, id=service_id)
            comment.save()
            messages.success(request, get_error_message("comment/added"))
            return redirect("service_detail", service_id=service_id)
        else:
            comment.service_center = get_object_or_404(ServiceCenter, id=center_id)
            comment.save()
            messages.success(request, get_error_message("comment/added"))
            return redirect("center_detail", center_id=center_id)

    if service_id:
        return redirect("service_detail", service_id=service_id)
    return redirect("center_detail", center_id=center_id)


@login_required
def edit_comment(request: HttpRequest, comment_id: int) -> HttpResponse:
    """Edit a comment. POST only. Owner-only, within 24h of posting."""
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method != "POST":
        return HttpResponse(status=405)

    if comment.is_deleted:
        messages.error(request, get_error_message("comment/cannot-edit-deleted"))
        return _comment_redirect(comment)

    if comment.user_id != request.user.id:
        messages.error(request, get_error_message("comment/owner-only"))
        return _comment_redirect(comment)

    if not comment.can_be_edited_by(request.user):
        messages.error(request, get_error_message("comment/edit-expired"))
        return _comment_redirect(comment)

    text = request.POST.get("text", "").strip()
    if not text:
        return _comment_redirect(comment)

    comment.text = text
    comment.edited_at = timezone.now()
    comment.save(update_fields=["text", "edited_at", "updated_at"])
    messages.success(request, get_error_message("comment/updated"))
    return _comment_redirect(comment)


@login_required
def delete_comment(request: HttpRequest, comment_id: int) -> HttpResponse:
    """Soft-delete a comment. POST only. Owner or staff."""
    comment = get_object_or_404(Comment, id=comment_id)

    if request.method != "POST":
        return HttpResponse(status=405)

    if comment.is_deleted:
        return _comment_redirect(comment)

    if comment.user_id != request.user.id and not request.user.is_staff:
        messages.error(request, get_error_message("comment/owner-only"))
        return _comment_redirect(comment)

    comment.deleted_by = request.user
    comment.save(update_fields=["deleted_by", "updated_at"])
    messages.success(request, get_error_message("comment/deleted"))
    return _comment_redirect(comment)


def _comment_redirect(comment: Comment) -> HttpResponse:
    """Redirect back to the page containing *comment*."""
    if comment.service_id:
        return redirect("service_detail", service_id=comment.service_id)
    return redirect("center_detail", center_id=comment.service_center_id)


def center_detail(request: HttpRequest, center_id: int) -> HttpResponse:
    """Show details for a single ServiceCenter.

    Publicly accessible. Shows center info, map, ratings, and comments.
    """
    center: ServiceCenter = get_object_or_404(
        ServiceCenter.objects.prefetch_related("services"), id=center_id
    )

    ratings = center.ratings.all()
    rating_agg = ratings.aggregate(avg=Avg("score"), cnt=Count("id"))
    avg_rating = rating_agg["avg"]
    rating_count = rating_agg["cnt"]

    user_center_rating = None
    if request.user.is_authenticated:
        user_center_rating = CenterRating.objects.filter(
            user=request.user, service_center=center
        ).first()

    top_level_comments = (
        Comment.objects.filter(service_center=center, parent__isnull=True)
        .select_related("user", "deleted_by")
        .prefetch_related(
            "replies__user", "replies__deleted_by", "reactions", "replies__reactions"
        )
    )

    comment_page = int(request.GET.get("comment_page", 1))
    comment_paginator = Paginator(top_level_comments, COMMENTS_PER_PAGE)
    comment_page_obj = comment_paginator.get_page(comment_page)
    has_more_comments = comment_page_obj.has_next()

    from .models import CommentReaction

    comment_reaction_data = {}
    all_comments = list(comment_page_obj) + [
        r for c in comment_page_obj for r in c.replies.all()
    ]
    for c in all_comments:
        likes = 0
        dislikes = 0
        user_rx = None
        user_id = request.user.id if request.user.is_authenticated else None
        for rx in c.reactions.all():
            if rx.value == CommentReaction.LIKE:
                likes += 1
            elif rx.value == CommentReaction.DISLIKE:
                dislikes += 1
            if user_rx is None and user_id and rx.user_id == user_id:
                user_rx = rx.value
        comment_reaction_data[c.id] = (likes, dislikes, user_rx)

    center_locations = get_center_locations(ServiceCenter.objects.filter(id=center.id))

    comment_form = None
    rating_form = None
    if request.user.is_authenticated:
        comment_form = CommentForm()
        rating_form = CenterRatingForm()

    return render(
        request,
        "services/center_detail.html",
        {
            "center": center,
            "services": center.services.all(),
            "center_locations": center_locations,
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
            "rating_count": rating_count,
            "user_center_rating": user_center_rating,
            "comments": comment_page_obj,
            "has_more_comments": has_more_comments,
            "comment_page": comment_page,
            "comment_form": comment_form,
            "rating_form": rating_form,
            "comment_reaction_data": comment_reaction_data,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "خدمات", "url": "/services/"},
                *[
                    {
                        "label": svc.name,
                        "url": f"/service/{svc.id}/",
                    }
                    for svc in center.services.all()
                ],
                {"label": center.name},
            ],
        },
    )


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
@login_required
def submit_center_rating(request: HttpRequest, center_id: int) -> HttpResponse:
    """Submit or update a rating for a service center.

    POST only: validates :class:`CenterRatingForm`, creates or updates the rating.
    If comment text is provided, also creates a Comment linked to the center.
    """
    if request.method != "POST":
        return redirect("center_detail", center_id=center_id)

    center = get_object_or_404(ServiceCenter, id=center_id)
    form = CenterRatingForm(request.POST)
    if form.is_valid():
        rating, created = CenterRating.objects.update_or_create(
            user=request.user,
            service_center=center,
            defaults={"score": int(form.cleaned_data["score"])},
        )
        if created:
            messages.success(request, get_error_message("center-rating/added"))
        else:
            messages.success(request, get_error_message("center-rating/updated"))

    return redirect("center_detail", center_id=center_id)


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def submit_report(request: HttpRequest) -> HttpResponse:
    """Submit a report about incorrect or outdated information.

    POST with JSON body: ``{"reason": str, "description": str, "target_type": str,
    "target_id": int}``.  Returns JSON for AJAX callers, redirects for plain forms.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": get_error_message("report/login-required")},
            status=401,
        )

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    try:
        data = (
            json.loads(request.body)
            if request.content_type == "application/json"
            else request.POST
        )
    except json.JSONDecodeError:
        data = request.POST

    target_type = data.get("target_type", "")
    target_id = data.get("target_id") or data.get("target_id")
    reason = data.get("reason", "")
    description = data.get("description", "")

    if target_type not in dict(InfoReport.ReportTarget.choices):
        msg = get_error_message("report/invalid-target")
        if is_ajax:
            return JsonResponse({"error": msg}, status=400)
        messages.error(request, msg)
        return redirect("home")

    try:
        target_id = int(target_id)
    except (TypeError, ValueError):
        msg = get_error_message("report/not-found")
        if is_ajax:
            return JsonResponse({"error": msg}, status=400)
        messages.error(request, msg)
        return redirect("home")

    if target_type == "service":
        target = get_object_or_404(Service, id=target_id)
        redirect_url = f"/service/{target_id}/"
    else:
        target = get_object_or_404(ServiceCenter, id=target_id)
        redirect_url = f"/center/{target_id}/"

    valid_reasons = dict(InfoReport.ReportReason.choices)
    if reason not in valid_reasons:
        reason = InfoReport.ReportReason.OTHER

    existing = InfoReport.objects.filter(
        user=request.user,
        target_type=target_type,
        service=target if target_type == "service" else None,
        service_center=target if target_type == "center" else None,
        reason=reason,
    ).first()

    if existing:
        msg = get_error_message("report/duplicate")
        if is_ajax:
            return JsonResponse({"error": msg}, status=409)
        messages.warning(request, msg)
        return redirect(redirect_url)

    InfoReport.objects.create(
        user=request.user,
        target_type=target_type,
        service=target if target_type == "service" else None,
        service_center=target if target_type == "center" else None,
        reason=reason,
        description=description,
    )

    msg = get_error_message("report/submitted")
    if is_ajax:
        return JsonResponse({"message": msg})
    messages.success(request, msg)
    return redirect(redirect_url)


def suggest_closest_center(request: HttpRequest, service_id: int) -> HttpResponse:
    """API endpoint: find the closest center based on browser geolocation.

    POST with JSON body ``{"lat": float, "lng": float}``.
    Returns JSON with the closest center details.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    import json

    try:
        data = json.loads(request.body)
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse(
            {"error": get_error_message("geolocation/invalid-coordinates")},
            status=400,
        )

    from django.contrib.gis.db.models.functions import Distance
    from django.contrib.gis.geos import Point

    user_point = Point(lng, lat, srid=4326)
    centers = (
        ServiceCenter.objects.filter(
            services__id=service_id,
            coordinate__isnull=False,
        )
        .annotate(distance=Distance("coordinate", user_point))
        .order_by("distance")[:1]
    )

    if not centers:
        return JsonResponse({"center": None})

    center = centers[0]
    phones = list(center.phones.values_list("phone", flat=True)[:3])
    return JsonResponse(
        {
            "center": {
                "id": center.id,
                "name": center.name,
                "address": center.address,
                "phones": phones,
                "distance_km": round(center.distance.km, 2),
                "map_url": center.get_map_url(),
                "lat": center.coordinate.y,
                "lng": center.coordinate.x,
            }
        }
    )


def load_centers(request: HttpRequest, service_id: int) -> JsonResponse:
    """API endpoint: load more centers for a service with pagination.

    GET with query params ``page`` (default 1) and ``per_page`` (default 5).
    Centers are ordered by proximity to the user's profile city (or Tehran
    for anonymous users), then by average rating.
    """
    service = get_object_or_404(Service, id=service_id)
    page = int(request.GET.get("page", 1))
    per_page = min(int(request.GET.get("per_page", 5)), 20)

    qs = ServiceCenter.objects.filter(services=service)

    annotate_rating = Avg("ratings__score")
    qs = qs.annotate(avg_score=annotate_rating)

    user_city = get_default_city()
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            user_city = profile.city
        except UserProfile.DoesNotExist:
            pass

    coord_center = qs.filter(
        city__icontains=user_city, coordinate__isnull=False
    ).first()

    if coord_center:
        from django.contrib.gis.db.models.functions import Distance

        qs = qs.annotate(
            city_distance=Distance("coordinate", coord_center.coordinate),
            is_in_city=Count("id", filter=Q(city__icontains=user_city)),
        ).order_by(
            "-is_in_city",
            "city_distance",
            F("avg_score").desc(nulls_last=True),
        )
    else:
        qs = qs.annotate(
            is_in_city=Count("id", filter=Q(city__icontains=user_city)),
        ).order_by(
            "-is_in_city",
            F("avg_score").desc(nulls_last=True),
        )

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    centers_data = []
    for center in page_obj:
        score = getattr(center, "avg_score", None)
        phones = list(center.phones.values("phone", "label"))
        center_data = {
            "id": center.id,
            "name": center.name,
            "address": center.address,
            "city": center.city,
            "phones": phones,
            "working_hours": center.working_hours,
            "postal_code": center.postal_code,
            "map_url": center.get_map_url(),
            "avg_rating": round(score, 1) if score else None,
        }
        if center.coordinate is not None:
            center_data["lat"] = center.coordinate.y
            center_data["lng"] = center.coordinate.x
        centers_data.append(center_data)

    return JsonResponse(
        {
            "centers": centers_data,
            "has_next": page_obj.has_next(),
            "total_pages": paginator.num_pages,
        }
    )


def load_comments(
    request: HttpRequest, target_type: str, target_id: int
) -> JsonResponse:
    """API endpoint: load more top-level comments for a service or center.

    GET with query param ``page`` (default 2). Returns rendered HTML fragments.
    """
    from django.template.loader import render_to_string

    page = int(request.GET.get("page", 2))

    if target_type == "service":
        target = get_object_or_404(Service, id=target_id)
        qs = Comment.objects.filter(service=target, parent__isnull=True)
    elif target_type == "center":
        target = get_object_or_404(ServiceCenter, id=target_id)
        qs = Comment.objects.filter(service_center=target, parent__isnull=True)
    else:
        return JsonResponse({"error": "invalid target"}, status=400)

    qs = qs.select_related("user").prefetch_related(
        "replies__user", "reactions", "replies__reactions"
    )

    paginator = Paginator(qs, COMMENTS_PER_PAGE)
    page_obj = paginator.get_page(page)

    from .models import CommentReaction

    html_parts = []
    for comment in page_obj:
        likes_count = comment.reactions.filter(value=CommentReaction.LIKE).count()
        dislikes_count = comment.reactions.filter(value=CommentReaction.DISLIKE).count()
        user_reaction = None
        if request.user.is_authenticated:
            reaction = comment.reactions.filter(user=request.user).first()
            user_reaction = reaction.value if reaction else None
        comment_reaction_data = {
            comment.id: (likes_count, dislikes_count, user_reaction),
        }
        html_parts.append(
            render_to_string(
                "services/partials/comment.html",
                {
                    "comment": comment,
                    "depth": 0,
                    "user": request.user,
                    "comment_reaction_data": comment_reaction_data,
                },
                request=request,
            )
        )

    return JsonResponse(
        {
            "html": "".join(html_parts),
            "has_next": page_obj.has_next(),
        }
    )


def cities_api(request: HttpRequest) -> JsonResponse:
    """API endpoint: return cities with service center counts.

    GET ``/api/cities/`` returns the top cities ordered by center count.
    Query params:

    - ``page`` (default 1): page number
    - ``per_page`` (default 20): results per page
    - ``search``: filter cities by name (case-insensitive contains)
    - ``city``: return a single city by exact name
    """
    page = int(request.GET.get("page", 1))
    per_page = min(int(request.GET.get("per_page", 20)), 50)
    search = request.GET.get("search", "").strip()
    single_city = request.GET.get("city", "").strip()

    qs = (
        ServiceCenter.objects.values("city")
        .annotate(center_count=Count("id"))
        .order_by("-center_count")
    )

    if single_city:
        qs = qs.filter(city__iexact=single_city)
        cities_data = [
            {"name": c["city"], "center_count": c["center_count"]} for c in qs[:1]
        ]
        return JsonResponse({"cities": cities_data, "has_next": False, "page": 1})

    if search:
        qs = qs.filter(city__icontains=search)

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    cities_data = [
        {"name": c["city"], "center_count": c["center_count"]} for c in page_obj
    ]

    return JsonResponse(
        {
            "cities": cities_data,
            "has_next": page_obj.has_next(),
            "page": page,
        }
    )


def robots_txt(request: HttpRequest) -> HttpResponse:
    """Serve robots.txt."""
    from django.conf import settings

    return HttpResponse(
        f"User-agent: *\nAllow: /\nSitemap: {settings.SITE_URL}/sitemap.xml\n",
        content_type="text/plain",
    )


def sitemap_xml(request: HttpRequest) -> HttpResponse:
    """Generate a simple sitemap.xml listing all public pages."""
    from django.conf import settings
    from django.urls import reverse

    from .models import Service, ServiceCenter

    site_url = settings.SITE_URL
    pages = [
        ("home", None, "0.9"),
        ("about", None, "0.7"),
        ("contact", None, "0.6"),
        ("faq", None, "0.7"),
        ("services_list", None, "0.8"),
    ]
    urls = ""
    for name, arg, priority in pages:
        url = (
            site_url + reverse(name)
            if arg is None
            else site_url + reverse(name, args=[arg])
        )
        urls += f"<url><loc>{url}</loc><priority>{priority}</priority></url>\n"
    for service in Service.objects.all().iterator():
        url = site_url + reverse("service_detail", args=[service.id])
        urls += f"<url><loc>{url}</loc><priority>0.6</priority></url>\n"
    for center in ServiceCenter.objects.all().iterator():
        url = site_url + reverse("center_detail", args=[center.id])
        urls += f"<url><loc>{url}</loc><priority>0.5</priority></url>\n"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>"
    )
    return HttpResponse(xml, content_type="application/xml")


@staff_member_required
def admin_stats(request: HttpRequest) -> HttpResponse:
    """Admin dashboard with usage statistics (staff only).

    Displays model counts, recent activity, popular services,
    top-rated centers, and weekly trend charts.

    The expensive aggregate queries are cached for 5 minutes to
    avoid repeated full-table scans on every page load.
    """
    STATS_CACHE_KEY = "admin_stats_data"
    STATS_CACHE_TTL = 300  # 5 minutes

    cached = cache.get(STATS_CACHE_KEY)
    if cached is not None:
        return render(request, "services/admin_stats.html", cached)

    now = timezone.now()
    twelve_weeks_ago = now - timedelta(weeks=12)

    overview = {
        "total_users": User.objects.count(),
        "total_services": Service.objects.count(),
        "total_centers": ServiceCenter.objects.count(),
        "total_comments": Comment.objects.count(),
        "total_ratings": CenterRating.objects.count(),
        "total_bookmarks": Bookmark.objects.count(),
        "total_contact_messages": ContactMessage.objects.count(),
        "total_faqs": FAQ.objects.count(),
    }

    recent_users = User.objects.order_by("-date_joined")[:10]
    recent_comments = Comment.objects.select_related(
        "user", "service", "service_center"
    ).order_by("-created_at")[:10]

    popular_services = Service.objects.annotate(
        comment_count=Count("comments")
    ).order_by("-comment_count")[:10]

    top_centers = (
        ServiceCenter.objects.annotate(
            avg_rating=Avg("ratings__score"),
            rating_count=Count("ratings"),
        )
        .filter(rating_count__gt=0)
        .order_by("-avg_rating")[:10]
    )

    # --- Chart data: weekly aggregations ---
    week_fmt = "%Y-%m-%d"

    reg_by_week = (
        User.objects.filter(date_joined__gte=twelve_weeks_ago)
        .annotate(week=TruncWeek("date_joined"))
        .values("week")
        .annotate(count=Count("id"))
        .order_by("week")
    )

    comments_by_week = (
        Comment.objects.filter(created_at__gte=twelve_weeks_ago)
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(count=Count("id"))
        .order_by("week")
    )

    ratings_by_week = (
        CenterRating.objects.filter(created_at__gte=twelve_weeks_ago)
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(count=Count("id"))
        .order_by("week")
    )

    chart_reg = json.dumps(
        [
            {"week": r["week"].strftime(week_fmt), "count": r["count"]}
            for r in reg_by_week
        ]
    )
    chart_comments = json.dumps(
        [
            {"week": r["week"].strftime(week_fmt), "count": r["count"]}
            for r in comments_by_week
        ]
    )
    chart_ratings = json.dumps(
        [
            {"week": r["week"].strftime(week_fmt), "count": r["count"]}
            for r in ratings_by_week
        ]
    )
    chart_services = json.dumps(
        [{"name": s.name, "count": s.comment_count} for s in popular_services]
    )

    context = {
        "overview": overview,
        "recent_users": recent_users,
        "recent_comments": recent_comments,
        "popular_services": popular_services,
        "top_centers": top_centers,
        "chart_reg": chart_reg,
        "chart_comments": chart_comments,
        "chart_ratings": chart_ratings,
        "chart_services": chart_services,
    }

    cache.set(STATS_CACHE_KEY, context, STATS_CACHE_TTL)

    return render(request, "services/admin_stats.html", context)


NESHAN_SEARCH_URL = "https://api.neshan.org/v1/search"


@staff_member_required
def neshan_search(request: HttpRequest) -> JsonResponse:
    """Proxy the Neshan search API to keep the API key server-side.

    Accepts ``term``, ``lat``, and ``lng`` query parameters and forwards
    them to ``api.neshan.org/v1/search``.  Returns the Neshan response
    as-is (JSON), or an error JSON on failure.
    """
    term = request.GET.get("term", "").strip()
    lat = request.GET.get("lat", "").strip()
    lng = request.GET.get("lng", "").strip()

    if not term or not lat or not lng:
        return JsonResponse(
            {"error": "term, lat, and lng are required."},
            status=400,
        )

    api_key = getattr(django_settings, "NESHAN_API_KEY", "")
    if not api_key:
        return JsonResponse(
            {"error": "NESHAN_API_KEY is not configured on the server."},
            status=503,
        )

    params = urllib.parse.urlencode({"term": term, "lat": lat, "lng": lng})
    url = f"{NESHAN_SEARCH_URL}?{params}"

    req = urllib.request.Request(url, headers={"Api-Key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
            return JsonResponse(data, safe=False)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return JsonResponse(
            {"error": f"Neshan API error ({exc.code})", "detail": body},
            status=exc.code,
        )
    except (urllib.error.URLError, TimeoutError):
        return JsonResponse(
            {"error": "Could not reach the Neshan search API."},
            status=502,
        )


EXPORTABLE_MODELS = [
    Service,
    ServiceCenter,
    ServiceCenterPhone,
    FAQ,
    UserProfile,
    ContactMessage,
    Comment,
    CenterRating,
    Bookmark,
    InfoReport,
]

IMPORT_ORDER = [
    Service,
    FAQ,
    UserProfile,
    ContactMessage,
    ServiceCenter,
    ServiceCenterPhone,
    Comment,
    CenterRating,
    Bookmark,
    InfoReport,
    PhoneVerification,
]


class _ExportEncoder(json.JSONEncoder):
    """Handle datetime and other non-serializable types."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Point):
            return f"{o.y},{o.x}"
        return super().default(o)


def _model_to_dict(obj):
    """Convert a model instance to a flat dictionary."""
    data = {}
    for field in obj._meta.get_fields():
        if field.many_to_many and not field.auto_created:
            data[field.attname] = list(
                getattr(obj, field.attname).values_list("pk", flat=True)
            )
        elif hasattr(field, "attname"):
            value = getattr(obj, field.attname, None)
            if isinstance(value, Point):
                value = f"{value.y},{value.x}"
            data[field.attname] = value
    if hasattr(obj, "pk"):
        data["pk"] = obj.pk
    return data


@staff_member_required
def admin_data_transfer(request: HttpRequest) -> HttpResponse:
    """Admin page for bulk export/import of selected models.

    Export: pick models and format, download a JSON/CSV file.
    Import: upload a JSON file produced by export, optionally dry-run.
    """
    model_choices = []
    for model in EXPORTABLE_MODELS:
        label = model._meta.label
        model_choices.append(
            {
                "value": label,
                "label": model._meta.verbose_name.title(),
                "count": model.objects.count(),
            }
        )

    context = {
        "model_choices": model_choices,
        "title": "Bulk Data Export / Import",
    }

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "export":
            selected_labels = request.POST.getlist("models")
            fmt = request.POST.get("format", "json")

            selected_models = [
                m for m in EXPORTABLE_MODELS if m._meta.label in selected_labels
            ]
            if not selected_models:
                context["error"] = "No models selected."
                return render(request, "services/admin_data_transfer.html", context)

            if fmt == "json":
                result = []
                for model in selected_models:
                    label = model._meta.label
                    for obj in model.objects.all():
                        record = _model_to_dict(obj)
                        record["_model"] = label
                        result.append(record)
                content = json.dumps(
                    result, ensure_ascii=False, indent=2, cls=_ExportEncoder
                )
                content_type = "application/json"
                ext = "json"
            else:
                rows = []
                for model in selected_models:
                    label = model._meta.label
                    for obj in model.objects.all():
                        row = _model_to_dict(obj)
                        row["_model"] = label
                        rows.append(row)
                if not rows:
                    context["error"] = "No data to export."
                    return render(request, "services/admin_data_transfer.html", context)
                all_keys = []
                seen = set()
                for row in rows:
                    for key in row:
                        if key not in seen:
                            all_keys.append(key)
                            seen.add(key)
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=all_keys)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
                content = buf.getvalue()
                content_type = "text/csv"
                ext = "csv"

            response = HttpResponse(content, content_type=content_type)
            filename = f"agahyar_export.{ext}"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        elif action == "import":
            upload_file = request.FILES.get("import_file")
            dry_run = request.POST.get("dry_run") == "on"

            if not upload_file:
                context["error"] = "No file uploaded."
                return render(request, "services/admin_data_transfer.html", context)

            max_import_size = 10 * 1024 * 1024  # 10 MB
            if upload_file.size > max_import_size:
                context["error"] = "File is too large. Maximum allowed size is 10 MB."
                return render(request, "services/admin_data_transfer.html", context)

            try:
                raw = upload_file.read().decode("utf-8")
                data = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                context["error"] = f"Invalid JSON file: {exc}"
                return render(request, "services/admin_data_transfer.html", context)

            if not isinstance(data, list):
                context["error"] = "Expected a JSON array of records."
                return render(request, "services/admin_data_transfer.html", context)

            max_import_records = 10000
            if len(data) > max_import_records:
                context["error"] = (
                    f"File contains {len(data):,} records. "
                    f"Maximum allowed is {max_import_records:,}."
                )
                return render(request, "services/admin_data_transfer.html", context)

            model_map = {m._meta.label: m for m in IMPORT_ORDER}
            order_map = {m._meta.label: i for i, m in enumerate(IMPORT_ORDER)}
            data.sort(
                key=lambda r: order_map.get(r.get("_model", ""), len(IMPORT_ORDER))
            )

            created = 0
            updated = 0
            skipped = 0
            errors = []
            m2m_pending = []

            for record in data:
                model_label = record.get("_model")
                if not model_label or model_label not in model_map:
                    skipped += 1
                    continue

                model = model_map[model_label]
                fields = {k: v for k, v in record.items() if k != "_model"}
                pk = fields.pop("pk", None)

                m2m_fields = {}
                for field in model._meta.get_fields():
                    if field.many_to_many and not field.auto_created:
                        attname = field.attname
                        if attname in fields:
                            m2m_fields[attname] = fields.pop(attname)

                if "coordinate" in fields and isinstance(fields["coordinate"], str):
                    try:
                        lat, lng = fields["coordinate"].split(",")
                        fields["coordinate"] = Point(float(lng), float(lat), srid=4326)
                    except (ValueError, AttributeError):
                        fields["coordinate"] = None

                if dry_run:
                    created += 1
                    continue

                try:
                    obj, is_new = model.objects.update_or_create(pk=pk, defaults=fields)
                    if is_new:
                        created += 1
                    else:
                        updated += 1
                    if m2m_fields:
                        m2m_pending.append((obj, m2m_fields, model_label))
                except Exception as exc:
                    errors.append(f"{model_label} pk={pk}: {exc}")
                    skipped += 1

            if not dry_run:
                for obj, m2m_fields, model_label in m2m_pending:
                    for attname, pk_list in m2m_fields.items():
                        if not isinstance(pk_list, list):
                            continue
                        try:
                            related_field = getattr(obj, attname)
                            related_model = related_field.model
                            valid_pks = related_model.objects.filter(
                                pk__in=pk_list
                            ).values_list("pk", flat=True)
                            related_field.set(valid_pks)
                        except Exception as exc:
                            errors.append(
                                f"M2M {model_label} pk={obj.pk} {attname}: {exc}"
                            )
                            skipped += 1

            verb = "Previewed" if dry_run else "Imported"
            context["import_result"] = {
                "verb": verb,
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "errors": errors,
            }
            return render(request, "services/admin_data_transfer.html", context)

    return render(request, "services/admin_data_transfer.html", context)
