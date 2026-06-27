from django.db import models
from django.contrib.auth.models import User

from services.validators import iranian_phone_number_validator

class Service(models.Model):
    name = models.CharField('نام خدمت', max_length=200)
    organization = models.CharField('سازمان مسئول', max_length=200)
    organization_address = models.CharField('آدرس سازمان', max_length=300, blank=True, null=True)
    documents = models.TextField('مدارک مورد نیاز (با | جدا شود)')
    steps = models.TextField('مراحل انجام (با | جدا شود)')
    cost = models.CharField('هزینه تقریبی', max_length=100, blank=True)
    duration = models.CharField('مدت زمان', max_length=100, blank=True)
    more_info_url = models.URLField('لینک اطلاعات بیشتر', blank=True, null=True)
    keywords = models.TextField('کلمات کلیدی', blank=True)
    
    def __str__(self):
        return self.name
    
    def get_documents_list(self):
        return self.documents.split('|') if self.documents else []
    
    def get_steps_list(self):
        return self.steps.split('|') if self.steps else []
    
    class Meta:
        verbose_name = 'خدمت'
        verbose_name_plural = 'خدمات'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    city = models.CharField('شهر محل سکونت', max_length=100)
    neighborhood = models.CharField('محله', max_length=100, blank=True, null=True)
    phone = models.CharField('شماره تماس', max_length=11, blank=True, validators=[iranian_phone_number_validator])
    
    def __str__(self):
        return f"{self.user.username} - {self.city} - {self.neighborhood}"
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'


class FAQ(models.Model):
    question = models.CharField('سوال', max_length=300)
    answer = models.TextField('پاسخ')
    category = models.CharField('دسته‌بندی', max_length=100, blank=True)
    order = models.IntegerField('ترتیب نمایش', default=0)
    
    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name = 'سوال متداول'
        verbose_name_plural = 'پرسش‌های متداول'
        ordering = ['order']


class ServiceCenter(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='centers')
    name = models.CharField('نام مرکز', max_length=200)
    address = models.TextField('آدرس کامل')
    city = models.CharField('شهر', max_length=100)
    phone = models.CharField('شماره تماس', max_length=11, blank=True)
    latitude = models.FloatField('عرض جغرافیایی', null=True, blank=True)
    longitude = models.FloatField('طول جغرافیایی', null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    class Meta:
        verbose_name = 'مرکز ارائه خدمت'
        verbose_name_plural = 'مراکز ارائه خدمت'


class ContactMessage(models.Model):
    name = models.CharField('نام', max_length=200)
    email = models.EmailField('ایمیل')
    message = models.TextField('پیام')
    created_at = models.DateTimeField('تاریخ', auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

    class Meta:
        verbose_name = 'پیام تماس'
        verbose_name_plural = 'پیام‌های تماس'