from typing import List

from django.urls import URLPattern, include, path

from . import views

urlpatterns: List[URLPattern] = [
    # ===== Core pages =====
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("service/<int:service_id>/", views.service_detail, name="service_detail"),
    path("services/", views.services_list, name="services_list"),
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
    path("logout/", views.logout_view, name="logout"),
    # django.contrib.auth.urls provides password-reset/* URLs
    # ===== Password reset =====
    path("password-reset/", include("django.contrib.auth.urls")),
]
