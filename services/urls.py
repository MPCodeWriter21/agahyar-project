from django.urls import path, include
from . import views

urlpatterns = [
    # ===== صفحات اصلی =====
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('services/', views.services_list, name='services_list'),
    
    # ===== صفحات جدید =====
    path('faq/', views.faq_view, name='faq'),
    path('nearby-centers/', views.nearby_centers_view, name='nearby_centers'),
    path('users/', views.show_users, name='show_users'),
    
    # ===== صفحات اطلاعاتی =====
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # ===== احراز هویت =====
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    # ===== بازیابی رمز عبور =====
    path('password-reset/', include('django.contrib.auth.urls')),

]