import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


NEAREST_CENTERS = {
    "تهران": {
        "سعادت‌آباد": {
            "صدور کارت ملی هوشمند": "ثبت احوال تهران - شعبه غرب",
            "صدور پاسپورت": "پلیس+۱۰ - شعبه ونک",
            "گواهینامه رانندگی پایه سوم": "مرکز تعویض پلاک غرب تهران",
            "مجوز کسب و کار": "اتاق اصناف تهران - شعبه مرکزی",
            "ثبت‌نام مدارس (سیدا)": "آموزش و پرورش منطقه ۵",
            "گواهی عدم سوء پیشینه": "پلیس+۱۰ - شعاع شمال",
            "ثبت‌نام دانشگاه (کنکور)": "سازمان سنجش - شعبه غرب",
            "دفاتر پیشخوان دولت": "دفتر پیشخوان - سعادت‌آباد",
            "بیمه تأمین اجتماعی": "تأمین اجتماعی - شعبه غرب",
            "ثبت‌نام خودرو": "سامانه خودرو - غرب",
        },
        "ونک": {
            "صدور کارت ملی هوشمند": "ثبت احوال تهران - شعبه شرق",
            "صدور پاسپورت": "پلیس+۱۰ - شعبه ونک",
            "گواهینامه رانندگی پایه سوم": "مرکز شماره ۲ راهنمایی و رانندگی",
            "مجوز کسب و کار": "اتاق اصناف تهران - شعبه مرکزی",
            "ثبت‌نام مدارس (سیدا)": "آموزش و پرورش منطقه ۱",
            "گواهی عدم سوء پیشینه": "پلیس+۱۰ - شعاع شمال",
            "ثبت‌نام دانشگاه (کنکور)": "سازمان سنجش - شعبه مرکزی",
            "دفاتر پیشخوان دولت": "دفتر پیشخوان - ونک",
            "بیمه تأمین اجتماعی": "تأمین اجتماعی - شعبه ونک",
            "ثبت‌نام خودرو": "سامانه خودرو - مرکزی",
        },
        "انقلاب": {
            "صدور کارت ملی هوشمند": "ثبت احوال تهران - شعبه مرکزی",
            "صدور پاسپورت": "پلیس+۱۰ - شعبه انقلاب",
            "گواهینامه رانندگی پایه سوم": "مرکز تعویض پلاک و گواهینامه تهران",
            "مجوز کسب و کار": "اتاق اصناف تهران - شعبه جنوب",
            "ثبت‌نام مدارس (سیدا)": "آموزش و پرورش منطقه ۷",
            "گواهی عدم سوء پیشینه": "پلیس+۱۰ - شعبه جنوب",
            "ثبت‌نام دانشگاه (کنکور)": "سازمان سنجش - شعبه مرکزی",
            "دفاتر پیشخوان دولت": "دفتر پیشخوان - انقلاب",
            "بیمه تأمین اجتماعی": "تأمین اجتماعی - شعبه مرکزی",
            "ثبت‌نام خودرو": "سامانه خودرو - مرکزی",
        },
        "پاسداران": {
            "صدور کارت ملی هوشمند": "ثبت احوال تهران - شعبه شرق",
            "صدور پاسپورت": "پلیس+۱۰ - شعاع شمال",
            "گواهینامه رانندگی پایه سوم": "مرکز تعویض پلاک و گواهینامه تهران",
            "مجوز کسب و کار": "اتاق اصناف تهران - شعبه مرکزی",
            "ثبت‌نام مدارس (سیدا)": "آموزش و پرورش منطقه ۱",
            "گواهی عدم سوء پیشینه": "پلیس+۱۰ - شعاع شمال",
            "ثبت‌نام دانشگاه (کنکور)": "سازمان سنجش - شعبه شمال",
            "دفاتر پیشخوان دولت": "دفتر پیشخوان - پاسداران",
            "بیمه تأمین اجتماعی": "تأمین اجتماعی - شعبه شمال",
            "ثبت‌نام خودرو": "سامانه خودرو - شمال",
        },
        "شهرک غرب": {
            "صدور کارت ملی هوشمند": "ثبت احوال تهران - شعبه غرب",
            "صدور پاسپورت": "پلیس+۱۰ - شعبه ونک",
            "گواهینامه رانندگی پایه سوم": "مرکز تعویض پلاک غرب تهران",
            "مجوز کسب و کار": "اتاق اصناف تهران - شعبه مرکزی",
            "ثبت‌نام مدارس (سیدا)": "آموزش و پرورش منطقه ۵",
            "گواهی عدم سوء پیشینه": "پلیس+۱۰ - شعاع شمال",
            "ثبت‌نام دانشگاه (کنکور)": "سازمان سنجش - شعبه غرب",
            "دفاتر پیشخوان دولت": "دفتر پیشخوان - شهرک غرب",
            "بیمه تأمین اجتماعی": "تأمین اجتماعی - شعبه غرب",
            "ثبت‌نام خودرو": "سامانه خودرو - غرب",
        },
    }
}


def get_nearest_center(service_name, city, neighborhood):
    if not service_name or not city or not neighborhood:
        return None
    
    try:
        if city in NEAREST_CENTERS:
            if neighborhood in NEAREST_CENTERS[city]:
                center_name = NEAREST_CENTERS[city][neighborhood].get(service_name)
                if center_name:
                    from .models import ServiceCenter
                    try:
                        return ServiceCenter.objects.get(name=center_name, city=city)
                    except ServiceCenter.DoesNotExist:
                        return ServiceCenter.objects.filter(
                            name__icontains=center_name.split(' - ')[0],
                            city=city
                        ).first()
    except Exception as e:
        logger.error(f"خطا در پیدا کردن نزدیک‌ترین مرکز: {e}")
    
    return None


def scrape_passport_info():
    try:
        url = "https://eplust.ir/"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            if soup.find(string=lambda t: t and 'پاسپورت' in t):
                return {
                    'source': 'سایت پلیس+۱۰',
                    'info': 'اطلاعات پاسپورت در سایت پلیس+۱۰ موجود است.'
                }
    except Exception as e:
        logger.error(f"خطا در اسکرپ: {e}")
    
    return {
        'source': 'دیتابیس داخلی',
        'info': 'هزینه پاسپورت عادی ۱۵۰,۰۰۰ تومان و فوری ۳۰۰,۰۰۰ تومان است.'
    }


def get_ai_suggestion(service_name, user_city):
    from .models import ServiceCenter
    try:
        centers = ServiceCenter.objects.filter(
            service__name__icontains=service_name,
            city__icontains=user_city
        )[:3]
        if centers.exists():
            return [{
                'name': c.name,
                'address': c.address,
                'phone': c.phone,
                'distance': 'نزدیک'
            } for c in centers]
    except Exception as e:
        logger.error(f"Error getting AI suggestion for '{service_name}' in '{user_city}': {e}")
    
    return [
        {'name': f'دفتر پیشخوان {user_city}', 'address': f'خیابان اصلی - {user_city}', 'phone': '---', 'distance': 'نزدیک'},
        {'name': f'اداره {service_name} در {user_city}', 'address': f'میدان مرکزی - {user_city}', 'phone': '---', 'distance': 'متوسط'},
    ]