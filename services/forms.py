from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .error_codes import get_error_message
from .validators import iranian_phone_number_validator

REQUIRED_MSG: str = get_error_message("field/required")
INVALID_EMAIL_MSG: str = get_error_message("field/invalid-email")
MAX_LENGTH_MSG: str = get_error_message("field/max-length")
INVALID_PHONE_MSG: str = get_error_message("field/invalid-phone")

CITY_CHOICES: list = [
    ("", "شهر خود را انتخاب کنید"),
    ("تهران", "تهران"),
    ("مشهد", "مشهد"),
    ("اصفهان", "اصفهان"),
    ("شیراز", "شیراز"),
    ("تبریز", "تبریز"),
    ("کرج", "کرج"),
    ("قم", "قم"),
    ("اهواز", "اهواز"),
    ("رشت", "رشت"),
    ("کرمانشاه", "کرمانشاه"),
    ("زاهدان", "زاهدان"),
    ("ارومیه", "ارومیه"),
]


class LoginForm(forms.Form):
    """Form used for user login (username + password)."""

    username = forms.CharField(
        label="نام کاربری",
        max_length=100,
        error_messages={"required": REQUIRED_MSG, "max_length": MAX_LENGTH_MSG},
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "نام کاربری خود را وارد کنید",
            }
        ),
    )
    password = forms.CharField(
        label="رمز عبور",
        error_messages={"required": REQUIRED_MSG},
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "رمز عبور خود را وارد کنید"}
        ),
    )


class RegisterForm(UserCreationForm):
    """Extended registration form with city, neighborhood and phone fields."""

    error_messages = {
        "password_mismatch": get_error_message("password/mismatch"),
    }

    email = forms.EmailField(
        label="ایمیل",
        error_messages={"required": REQUIRED_MSG, "invalid": INVALID_EMAIL_MSG},
    )
    city = forms.CharField(
        label="شهر محل سکونت",
        max_length=100,
        error_messages={"required": REQUIRED_MSG},
        widget=forms.Select(choices=CITY_CHOICES),
    )
    neighborhood = forms.CharField(
        label="محله",
        max_length=100,
        error_messages={"required": REQUIRED_MSG},
        widget=forms.TextInput(attrs={"placeholder": "مثال: سعادت‌آباد، ونک، ..."}),
    )
    phone = forms.CharField(
        label="شماره تماس",
        max_length=11,
        required=False,
        validators=[iranian_phone_number_validator],
        error_messages={"invalid": INVALID_PHONE_MSG},
        widget=forms.TextInput(attrs={"placeholder": "مثال: 09121234567"}),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "city",
            "neighborhood",
            "phone",
        ]


class ProfileForm(forms.Form):
    """Form for editing user profile (city, neighborhood, phone)."""

    city = forms.CharField(
        label="شهر محل سکونت",
        max_length=100,
        error_messages={"required": REQUIRED_MSG},
        widget=forms.Select(choices=CITY_CHOICES),
    )
    neighborhood = forms.CharField(
        label="محله",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "مثال: سعادت‌آباد، ونک، ..."}),
    )
    phone = forms.CharField(
        label="شماره تماس",
        max_length=11,
        required=False,
        validators=[iranian_phone_number_validator],
        error_messages={"invalid": INVALID_PHONE_MSG},
        widget=forms.TextInput(attrs={"placeholder": "مثال: 09121234567"}),
    )


class ContactForm(forms.Form):
    """Form for the contact-us page."""

    name = forms.CharField(
        label="نام و نام خانوادگی",
        max_length=200,
        error_messages={"required": REQUIRED_MSG, "max_length": MAX_LENGTH_MSG},
        widget=forms.TextInput(attrs={"placeholder": "نام خود را وارد کنید"}),
    )
    email = forms.EmailField(
        label="ایمیل",
        error_messages={"required": REQUIRED_MSG, "invalid": INVALID_EMAIL_MSG},
        widget=forms.EmailInput(attrs={"placeholder": "example@email.com"}),
    )
    message = forms.CharField(
        label="پیام شما",
        error_messages={"required": REQUIRED_MSG},
        widget=forms.Textarea(
            attrs={"rows": 5, "placeholder": "پیام خود را بنویسید..."}
        ),
    )
