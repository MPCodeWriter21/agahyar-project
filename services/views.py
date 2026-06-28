from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .error_codes import get_error_message
from .forms import CITY_CHOICES, ContactForm, LoginForm, ProfileForm, RegisterForm
from .models import FAQ, ContactMessage, Service, ServiceCenter, UserProfile
from .scraper import get_nearest_center


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


def register_view(request: HttpRequest) -> HttpResponse:
    """Handle user registration.

    If the user is already authenticated, redirect to home.
    On POST, validates :class:`RegisterForm`, creates the user and profile,
    logs the user in, and redirects to home.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            city = form.cleaned_data["city"]
            neighborhood = form.cleaned_data["neighborhood"]
            phone = form.cleaned_data.get("phone", "")
            save_user_profile(user.id, city, neighborhood, phone)
            login(request, user)
            messages.success(
                request, get_error_message("register/welcome", username=user.username)
            )
            return redirect("home")
    else:
        form = RegisterForm()

    return render(
        request, "services/register.html", {"form": form, "city_choices": CITY_CHOICES}
    )


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
                messages.success(
                    request,
                    get_error_message("register/welcome", username=user.username),
                )
                return redirect("home")
            messages.error(request, get_error_message("auth/invalid-credentials"))
    else:
        form = LoginForm()

    return render(request, "services/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log out the current user and redirect to login."""
    logout(request)
    return redirect("login")


def home(request: HttpRequest) -> HttpResponse:
    """Render the public home page with popular services and recent FAQs."""
    popular_services: QuerySet = Service.objects.all()[:6]
    faqs: QuerySet = FAQ.objects.all()[:5]
    return render(
        request,
        "services/home.html",
        {
            "popular_services": popular_services,
            "faqs": faqs,
        },
    )


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the authenticated user dashboard."""
    popular_services: QuerySet = Service.objects.all()[:6]
    faqs: QuerySet = FAQ.objects.all()[:5]
    return render(
        request,
        "services/dashboard.html",
        {
            "popular_services": popular_services,
            "faqs": faqs,
        },
    )


def search(request: HttpRequest) -> HttpResponse:
    """Search services by name, keywords or organization.

    Requires authentication. Results are paginated (12 per page).
    """
    if not request.user.is_authenticated:
        return redirect("login")
    query: str = request.GET.get("q", "").strip()
    results: QuerySet = Service.objects.none()
    if query:
        results = Service.objects.filter(
            Q(name__icontains=query)
            | Q(keywords__icontains=query)
            | Q(organization__icontains=query)
        ).order_by("id")
    paginator: Paginator = Paginator(results, 12)
    page_number: str = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "services/search.html",
        {"query": query, "page_obj": page_obj, "count": paginator.count},
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

    return render(
        request,
        "services/detail.html",
        {
            "service": service,
            "documents": service.get_documents_list(),
            "steps": service.get_steps_list(),
            "nearest_center": nearest_center,
            "user_city": user_city,
            "user_neighborhood": user_neighborhood,
        },
    )


def services_list(request: HttpRequest) -> HttpResponse:
    """List all services ordered by name, paginated (12 per page)."""
    all_services: QuerySet = Service.objects.all().order_by("name")
    paginator: Paginator = Paginator(all_services, 12)
    page_number: str = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(request, "services/list.html", {"page_obj": page_obj})


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
    return render(request, "services/show_users.html", {"users": users})


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Show and edit the current user's profile.

    GET: displays the profile data and an edit form.
    POST: saves profile changes (city, neighborhood, phone) or password.
    """
    profile: UserProfile | None = None
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        pass

    if request.method == "POST":
        if "update_profile" in request.POST:
            form = ProfileForm(request.POST)
            password_form = PasswordChangeForm(request.user)
            if form.is_valid():
                save_user_profile(
                    request.user.id,
                    form.cleaned_data["city"],
                    form.cleaned_data["neighborhood"],
                    form.cleaned_data.get("phone", ""),
                )
                messages.success(request, get_error_message("profile/updated"))
                return redirect("profile")
        elif "change_password" in request.POST:
            form = ProfileForm()
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, get_error_message("password/changed"))
                return redirect("profile")
    else:
        initial = {}
        if profile:
            initial = {
                "city": profile.city,
                "neighborhood": profile.neighborhood,
                "phone": profile.phone,
            }
        form = ProfileForm(initial=initial)
        password_form = PasswordChangeForm(request.user)

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
