"""URL configuration for the ``services`` application.

Maps all application routes: core pages, authentication
endpoints, bookmarks, ratings, and password reset flows.
"""

from typing import List

from django.contrib.auth import views as auth_views
from django.urls import URLPattern, path

from . import views

urlpatterns: List[URLPattern] = [
    # ===== SEO =====
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
    # ===== Core pages =====
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("search/", views.search, name="search"),
    path("service/<int:service_id>/", views.service_detail, name="service_detail"),
    path("services/", views.services_list, name="services_list"),
    # ===== Bookmarks & Ratings =====
    path("bookmarks/", views.bookmarks_list, name="bookmarks_list"),
    path("bookmark/<int:service_id>/", views.toggle_bookmark, name="toggle_bookmark"),
    path("rate/<int:service_id>/", views.submit_rating, name="submit_rating"),
    # ===== Supplementary pages =====
    path("profile/", views.profile_view, name="profile"),
    path("faq/", views.faq_view, name="faq"),
    path("nearby-centers/", views.nearby_centers_view, name="nearby_centers"),
    path("users/", views.show_users, name="show_users"),
    # ===== Informational pages =====
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    # ===== Authentication =====
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="app_logout"),
    # ===== Password reset =====
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="services/auth/password_reset_form.html",
            email_template_name="services/auth/password_reset_email.html",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="services/auth/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="services/auth/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="services/auth/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
