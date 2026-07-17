"""View functions for the Agahyar services application.

Covers authentication, dashboard, search, service detail,
bookmarks, ratings, profile, FAQ, contact, nearby centers,
and SEO endpoints, with rate limiting on sensitive views.
"""

import logging
from datetime import timedelta

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Q, QuerySet
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
    ProfileForm,
    RegisterForm,
    get_city_choices,
    get_default_city,
)
from .maps import get_center_locations, get_city_center
from .models import (
    FAQ,
    Bookmark,
    CenterRating,
    Comment,
    ContactMessage,
    PhoneVerification,
    Service,
    ServiceCenter,
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
                    {"form": form, "city_choices": get_city_choices()},
                )

            messages.success(request, get_error_message("otp/sent"))
            return redirect("verify_otp")
    else:
        form = RegisterForm()

    return render(
        request,
        "services/auth/register.html",
        {"form": form, "city_choices": get_city_choices()},
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

            otp_max_age = timedelta(
                minutes=getattr(django_settings, "OTP_EXPIRE_MINUTES", 5)
            )
            if timezone.now() - verification.created_at > otp_max_age:
                messages.error(request, get_error_message("otp/expired"))
                return render(
                    request,
                    "services/auth/verify_otp.html",
                    {"form": form, "phone": phone, "cooldown": cooldown},
                )

            if not verify_otp(verification.otp_code, otp_code):
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


@ratelimit(key="ip", rate="2/m", method="POST", block=False)
def resend_otp_api(request: HttpRequest) -> JsonResponse:
    """API endpoint for resending OTP codes via AJAX.

    POST: validates cooldown, generates a new OTP, sends it, and returns JSON
    with the remaining cooldown for the next resend.

    Rate limiting is checked but does not block -- the response body reports
    the error so the frontend can display it gracefully.
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

    was_limited = getattr(request, "view_limited", False)
    if was_limited:
        return JsonResponse(
            {"error": get_error_message("otp/too-many-resends")},
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
            q &= Q(centers__city__icontains=city_filter)
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
    user_city_for_centers = None
    if request.user.is_authenticated:
        try:
            profile: UserProfile = request.user.profile
            user_city = profile.city
            user_neighborhood = profile.neighborhood
            user_city_for_centers = profile.city
        except UserProfile.DoesNotExist:
            pass

    nearest_center = get_nearest_center(service.name, user_city, user_neighborhood)

    if not nearest_center:
        nearest_center = ServiceCenter.objects.filter(
            service=service, city__icontains=user_city
        ).first()

    centers_qs = ServiceCenter.objects.filter(service=service).annotate(
        avg_score=Avg("ratings__score")
    )

    if user_city_for_centers:
        city_centers = centers_qs.filter(city__icontains=user_city_for_centers)
        from django.contrib.gis.db.models.functions import Distance as DistFunc

        coord_center = city_centers.filter(coordinate__isnull=False).first()
        if coord_center:
            city_centers = city_centers.annotate(
                city_distance=DistFunc("coordinate", coord_center.coordinate)
            ).order_by(
                "city_distance",
                F("avg_score").desc(nulls_last=True),
            )
        else:
            city_centers = city_centers.order_by(F("avg_score").desc(nulls_last=True))
    else:
        city_centers = centers_qs.order_by(F("avg_score").desc(nulls_last=True))

    initial_centers = list(city_centers[:5])
    has_more_centers = city_centers.count() > 5

    center_locations = get_center_locations(city_centers)
    city_center = get_city_center(user_city)

    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(
            user=request.user, service=service
        ).exists()

    top_level_comments = (
        Comment.objects.filter(service=service, parent__isnull=True)
        .select_related("user", "deleted_by")
        .prefetch_related("replies__user", "replies__deleted_by")
    )

    comment_page = int(request.GET.get("comment_page", 1))
    comment_paginator = Paginator(top_level_comments, COMMENTS_PER_PAGE)
    comment_page_obj = comment_paginator.get_page(comment_page)
    has_more_comments = comment_page_obj.has_next()

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
    ).select_related("service")

    centers_by_service: dict = {}
    for center in all_centers:
        centers_by_service.setdefault(center.service.name, []).append(center)

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


def show_users(request: HttpRequest) -> HttpResponse:
    """List all users with their profile data."""
    if not request.user.is_authenticated:
        return redirect("login")
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

    if request.method == "POST":
        if "update_profile" in request.POST:
            form = ProfileForm(request.POST, user_id=request.user.id)
            password_form = PersianPasswordChangeForm(request.user)
            if form.is_valid():
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
            form = ProfileForm(initial=profile_initial)
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
        form = ProfileForm(initial=profile_initial)
        password_form = PersianPasswordChangeForm(request.user)

    return render(
        request,
        "services/profile.html",
        {
            "form": form,
            "password_form": password_form,
            "profile": profile,
            "city_choices": get_city_choices(),
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
    POST: toggles bookmark for the given service.
    """

    if request.method != "POST":
        return redirect("service_detail", service_id=service_id)

    service = get_object_or_404(Service, id=service_id)
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user, service=service
    )
    if not created:
        bookmark.delete()
        messages.success(request, get_error_message("bookmark/removed"))
    else:
        messages.success(request, get_error_message("bookmark/added"))

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
        ServiceCenter.objects.select_related("service"), id=center_id
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
        .prefetch_related("replies__user", "replies__deleted_by")
    )

    comment_page = int(request.GET.get("comment_page", 1))
    comment_paginator = Paginator(top_level_comments, COMMENTS_PER_PAGE)
    comment_page_obj = comment_paginator.get_page(comment_page)
    has_more_comments = comment_page_obj.has_next()

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
            "service": center.service,
            "center_locations": center_locations,
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
            "rating_count": rating_count,
            "user_center_rating": user_center_rating,
            "comments": comment_page_obj,
            "has_more_comments": has_more_comments,
            "comment_page": comment_page,
            "comment_form": comment_form,
            "rating_form": rating_form,
            "breadcrumbs": [
                {"label": "خانه", "url": "/"},
                {"label": "خدمات", "url": "/services/"},
                {
                    "label": center.service.name,
                    "url": f"/service/{center.service.id}/",
                },
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
            service_id=service_id,
            coordinate__isnull=False,
        )
        .annotate(distance=Distance("coordinate", user_point))
        .order_by("distance")[:1]
    )

    if not centers:
        return JsonResponse({"center": None})

    center = centers[0]
    return JsonResponse(
        {
            "center": {
                "id": center.id,
                "name": center.name,
                "address": center.address,
                "phone": center.phone,
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
    For authenticated users, centers are ordered by proximity if their profile
    city is known, otherwise by rating. For anonymous users, by rating.
    """
    service = get_object_or_404(Service, id=service_id)
    page = int(request.GET.get("page", 1))
    per_page = min(int(request.GET.get("per_page", 5)), 20)

    qs = ServiceCenter.objects.filter(service=service)

    annotate_rating = Avg("ratings__score")
    qs = qs.annotate(avg_score=annotate_rating)

    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            user_city = profile.city
        except UserProfile.DoesNotExist:
            user_city = None

        if user_city:
            from django.contrib.gis.db.models.functions import Distance

            city_qs = qs.filter(city__icontains=user_city, coordinate__isnull=False)
            coord_center = city_qs.first()
            if coord_center:
                qs = qs.filter(city__icontains=user_city)
                qs = qs.annotate(
                    city_distance=Distance("coordinate", coord_center.coordinate)
                ).order_by(
                    "city_distance",
                    F("avg_score").desc(nulls_last=True),
                )
            else:
                qs = qs.filter(city__icontains=user_city).order_by(
                    F("avg_score").desc(nulls_last=True)
                )
        else:
            qs = qs.order_by(F("avg_score").desc(nulls_last=True))
    else:
        qs = qs.order_by(F("avg_score").desc(nulls_last=True))

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    centers_data = []
    for center in page_obj:
        score = getattr(center, "avg_score", None)
        centers_data.append(
            {
                "id": center.id,
                "name": center.name,
                "address": center.address,
                "city": center.city,
                "phone": center.phone,
                "working_hours": center.working_hours,
                "postal_code": center.postal_code,
                "map_url": center.get_map_url(),
                "avg_rating": round(score, 1) if score else None,
            }
        )

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

    qs = qs.select_related("user").prefetch_related("replies__user")

    paginator = Paginator(qs, COMMENTS_PER_PAGE)
    page_obj = paginator.get_page(page)

    html_parts = []
    for comment in page_obj:
        html_parts.append(
            render_to_string(
                "services/partials/comment.html",
                {"comment": comment, "depth": 0, "user": request.user},
                request=request,
            )
        )

    return JsonResponse(
        {
            "html": "".join(html_parts),
            "has_next": page_obj.has_next(),
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
    for service in Service.objects.all():
        url = site_url + reverse("service_detail", args=[service.id])
        urls += f"<url><loc>{url}</loc><priority>0.6</priority></url>\n"
    for center in ServiceCenter.objects.all():
        url = site_url + reverse("center_detail", args=[center.id])
        urls += f"<url><loc>{url}</loc><priority>0.5</priority></url>\n"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>"
    )
    return HttpResponse(xml, content_type="application/xml")
