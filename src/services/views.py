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
from django.db.models import Avg, Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .error_codes import get_error_message
from .forms import (
    CITY_CHOICES,
    ContactForm,
    LoginForm,
    OTPVerifyForm,
    PersianPasswordChangeForm,
    ProfileForm,
    RatingForm,
    RegisterForm,
)
from .maps import get_center_locations, get_city_center
from .models import (
    FAQ,
    Bookmark,
    ContactMessage,
    PhoneVerification,
    Rating,
    Service,
    ServiceCenter,
    UserProfile,
)
from .otp import generate_otp, hash_otp, verify_otp
from .sms import SMSAPIError, get_sms_client
from .suggestion import get_nearest_center

logger = logging.getLogger(__name__)


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
                    {"form": form, "city_choices": CITY_CHOICES},
                )

            messages.success(request, get_error_message("otp/sent"))
            return redirect("verify_otp")
    else:
        form = RegisterForm()

    return render(
        request,
        "services/auth/register.html",
        {"form": form, "city_choices": CITY_CHOICES},
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
            "bookmarked_ids": bookmarked_ids,
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
        },
    )


def service_detail(request: HttpRequest, service_id: int) -> HttpResponse:
    """Show details for a single Service.

    Requires authentication. Attempts to determine the nearest service
    center based on the user's profile city and neighborhood.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    service: Service = get_object_or_404(Service, id=service_id)

    try:
        profile: UserProfile = request.user.profile
        user_city: str = profile.city
        user_neighborhood: str = profile.neighborhood
    except UserProfile.DoesNotExist:
        user_city = "تهران"
        user_neighborhood = ""

    nearest_center = get_nearest_center(service.name, user_city, user_neighborhood)

    if not nearest_center:
        nearest_center = ServiceCenter.objects.filter(
            service=service, city__icontains=user_city
        ).first()

    centers_in_city = ServiceCenter.objects.filter(
        service=service, city__icontains=user_city
    )
    center_locations = get_center_locations(centers_in_city)
    city_center = get_city_center(user_city)

    is_bookmarked = Bookmark.objects.filter(user=request.user, service=service).exists()

    ratings = (
        Rating.objects.filter(service=service)
        .select_related("user")
        .order_by("-created_at")
    )
    avg_rating = ratings.aggregate(Avg("score"))["score__avg"]
    user_rating = Rating.objects.filter(user=request.user, service=service).first()
    comments = [r for r in ratings if r.comment]

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
            "center_locations": center_locations,
            "city_center": city_center,
            "is_bookmarked": is_bookmarked,
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
            "rating_count": ratings.count(),
            "user_rating": user_rating,
            "comments": comments,
            "rating_form": RatingForm(),
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
        {"page_obj": page_obj, "bookmarked_ids": bookmarked_ids},
    )


def faq_view(request: HttpRequest) -> HttpResponse:
    """Display all FAQs ordered by their ``order`` field."""
    if not request.user.is_authenticated:
        return redirect("login")
    faqs: QuerySet = FAQ.objects.all().order_by("order")
    return render(request, "services/faq.html", {"faqs": faqs})


@login_required
def nearby_centers_view(request: HttpRequest) -> HttpResponse:
    """List nearby service centers grouped by service for the user's city.

    Requires authentication. Falls back to "تهران" if no profile exists.
    """
    try:
        profile: UserProfile = request.user.profile
        user_city: str = profile.city
        user_neighborhood: str = profile.neighborhood
    except UserProfile.DoesNotExist:
        user_city = "تهران"
        user_neighborhood = ""

    services: QuerySet = Service.objects.all()
    centers_by_service: dict = {}

    for service in services:
        centers: QuerySet = ServiceCenter.objects.filter(
            service=service, city__icontains=user_city
        )

        if centers.exists():
            nearest_center = get_nearest_center(
                service.name, user_city, user_neighborhood
            )

            centers_list: list = []
            for center in centers:
                center.is_nearest = False
                if nearest_center and center.id == nearest_center.id:
                    center.is_nearest = True
                centers_list.append(center)

            centers_by_service[service.name] = centers_list

    return render(
        request,
        "services/nearby_centers.html",
        {
            "centers_by_service": centers_by_service,
            "user_city": user_city,
            "user_neighborhood": user_neighborhood,
        },
    )


def show_users(request: HttpRequest) -> HttpResponse:
    """List all users with their profile data."""
    if not request.user.is_authenticated:
        return redirect("login")
    users: QuerySet = User.objects.select_related("profile").all().order_by("id")
    return render(request, "services/user_list.html", {"users": users})


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
            "city_choices": CITY_CHOICES,
        },
    )


def about(request: HttpRequest) -> HttpResponse:
    """Render the about page (public)."""
    return render(request, "services/about.html")


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

    return render(request, "services/contact.html", {"form": form})


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
    return render(request, "services/bookmarks.html", {"bookmarks": bookmarks})


@login_required
def submit_rating(request: HttpRequest, service_id: int) -> HttpResponse:
    """Submit or update a rating for a service.

    POST only: validates :class:`RatingForm`, creates or updates the rating.
    """
    if request.method != "POST":
        return redirect("service_detail", service_id=service_id)

    service = get_object_or_404(Service, id=service_id)
    form = RatingForm(request.POST)
    if form.is_valid():
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            service=service,
            defaults={
                "score": int(form.cleaned_data["score"]),
                "comment": form.cleaned_data.get("comment", ""),
            },
        )
        if created:
            messages.success(request, get_error_message("rating/added"))
        else:
            messages.success(request, get_error_message("rating/updated"))

    return redirect("service_detail", service_id=service_id)


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

    from .models import Service

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
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>"
    )
    return HttpResponse(xml, content_type="application/xml")
