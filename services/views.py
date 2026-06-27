from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Service, UserProfile, FAQ, ServiceCenter, ContactMessage
from .forms import LoginForm, RegisterForm, ContactForm, CITY_CHOICES
from .scraper import scrape_passport_info, get_ai_suggestion, get_nearest_center


def save_user_profile(user_id, city, neighborhood='', phone=''):
    UserProfile.objects.update_or_create(
        user_id=user_id,
        defaults={'city': city, 'neighborhood': neighborhood, 'phone': phone},
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            city = form.cleaned_data['city']
            neighborhood = form.cleaned_data['neighborhood']
            phone = form.cleaned_data.get('phone', '')
            save_user_profile(user.id, city, neighborhood, phone)
            login(request, user)
            messages.success(request, f'خوش آمدید {user.username}!')
            return redirect('home')
    else:
        form = RegisterForm()
    
    return render(request, 'services/register.html', {'form': form, 'city_choices': CITY_CHOICES})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'خوش آمدید {user.username}!')
                return redirect('home')
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    else:
        form = LoginForm()
    
    return render(request, 'services/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    popular_services = Service.objects.all()[:6]
    faqs = FAQ.objects.all()[:5]
    return render(request, 'services/home.html', {
        'popular_services': popular_services,
        'faqs': faqs,
    })


def search(request):
    if not request.user.is_authenticated:
        return redirect('login')
    query = request.GET.get('q', '').strip()
    results = Service.objects.none()
    if query:
        results = Service.objects.filter(
            Q(name__icontains=query) |
            Q(keywords__icontains=query) |
            Q(organization__icontains=query)
        ).order_by('id')
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'services/search.html', {
        'query': query,
        'page_obj': page_obj,
        'count': paginator.count
    })


def service_detail(request, service_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    service = get_object_or_404(Service, id=service_id)
    
    try:
        profile = request.user.profile
        user_city = profile.city
        user_neighborhood = profile.neighborhood
    except UserProfile.DoesNotExist:
        user_city = 'تهران'
        user_neighborhood = ''
    
    nearest_center = get_nearest_center(service.name, user_city, user_neighborhood)
    
    if not nearest_center:
        nearest_center = ServiceCenter.objects.filter(
            service=service,
            city__icontains=user_city
        ).first()
    
    return render(request, 'services/detail.html', {
        'service': service,
        'documents': service.get_documents_list(),
        'steps': service.get_steps_list(),
        'nearest_center': nearest_center,
        'user_city': user_city,
        'user_neighborhood': user_neighborhood,
    })


def services_list(request):
    if not request.user.is_authenticated:
        return redirect('login')
    all_services = Service.objects.all().order_by('name')
    paginator = Paginator(all_services, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'services/list.html', {'page_obj': page_obj})


def faq_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    faqs = FAQ.objects.all().order_by('order')
    return render(request, 'services/faq.html', {'faqs': faqs})


@login_required
def nearby_centers_view(request):
    try:
        profile = request.user.profile
        user_city = profile.city
        user_neighborhood = profile.neighborhood
    except UserProfile.DoesNotExist:
        user_city = 'تهران'
        user_neighborhood = ''
    
    services = Service.objects.all()
    centers_by_service = {}
    
    for service in services:
        centers = ServiceCenter.objects.filter(
            service=service,
            city__icontains=user_city
        )
        
        if centers.exists():
            nearest_center = get_nearest_center(service.name, user_city, user_neighborhood)
            
            centers_list = []
            for center in centers:
                center.is_nearest = False
                if nearest_center and center.id == nearest_center.id:
                    center.is_nearest = True
                centers_list.append(center)
            
            centers_by_service[service.name] = centers_list
    
    return render(request, 'services/nearby_centers.html', {
        'centers_by_service': centers_by_service,
        'user_city': user_city,
        'user_neighborhood': user_neighborhood,
    })


def show_users(request):
    if not request.user.is_authenticated:
        return redirect('login')
    users = User.objects.select_related('profile').all().order_by('id')
    return render(request, 'services/show_users.html', {'users': users})


def about(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'services/about.html')


def contact(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message'],
            )
            messages.success(request, 'پیام شما با موفقیت ارسال شد.')
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'services/contact.html', {'form': form})