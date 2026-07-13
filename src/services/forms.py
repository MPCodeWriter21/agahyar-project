"""Django forms for the Agahyar services application.

Provides ``LoginForm``, ``RegisterForm``, ``ProfileForm``,
``RatingForm``, and ``ContactForm`` with Persian error messages
and Iranian phone number validation.
"""

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User

from .error_codes import get_error_message
from .models import UserProfile
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
    remember_me = forms.BooleanField(
        label="مرا به خاطر بسپار",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "remember-me-checkbox"}),
    )


class RegisterForm(UserCreationForm):
    """Extended registration form with name, city, neighborhood and phone fields."""

    error_messages = {
        "password_mismatch": get_error_message("password/mismatch"),
    }

    first_name = forms.CharField(
        label="نام",
        max_length=30,
        error_messages={"required": REQUIRED_MSG},
        widget=forms.TextInput(attrs={"placeholder": "نام خود را وارد کنید"}),
    )
    last_name = forms.CharField(
        label="نام خانوادگی",
        max_length=30,
        error_messages={"required": REQUIRED_MSG},
        widget=forms.TextInput(attrs={"placeholder": "نام خانوادگی خود را وارد کنید"}),
    )
    email = forms.EmailField(
        label="ایمیل",
        required=False,
        error_messages={"invalid": INVALID_EMAIL_MSG},
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
        validators=[iranian_phone_number_validator],
        error_messages={"required": REQUIRED_MSG, "invalid": INVALID_PHONE_MSG},
        widget=forms.TextInput(attrs={"placeholder": "مثال: 09121234567"}),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                get_error_message("username/duplicate"),
                code="duplicate_username",
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(get_error_message("email/duplicate"))
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and UserProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError(get_error_message("phone/duplicate"))
        return phone

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "city",
            "neighborhood",
            "phone",
        ]


class ProfileForm(forms.Form):
    """Form for editing user profile (name, email, city, neighborhood, phone)."""

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop("user_id", None)
        super().__init__(*args, **kwargs)

    first_name = forms.CharField(
        label="نام",
        max_length=30,
        error_messages={"required": REQUIRED_MSG},
    )
    last_name = forms.CharField(
        label="نام خانوادگی",
        max_length=30,
        error_messages={"required": REQUIRED_MSG},
    )
    email = forms.EmailField(
        label="ایمیل",
        required=False,
        error_messages={"invalid": INVALID_EMAIL_MSG},
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
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "مثال: سعادت‌آباد، ونک، ..."}),
    )
    phone = forms.CharField(
        label="شماره تماس",
        max_length=11,
        validators=[iranian_phone_number_validator],
        error_messages={"required": REQUIRED_MSG, "invalid": INVALID_PHONE_MSG},
        widget=forms.TextInput(attrs={"placeholder": "مثال: 09121234567"}),
    )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone:
            qs = UserProfile.objects.filter(phone=phone)
            if self.user_id:
                qs = qs.exclude(user_id=self.user_id)
            if qs.exists():
                raise forms.ValidationError(get_error_message("phone/duplicate"))
        return phone


class PersianPasswordChangeForm(PasswordChangeForm):
    """PasswordChangeForm with Persian error messages."""

    error_messages = {
        "password_mismatch": get_error_message("password/mismatch"),
        "password_incorrect": get_error_message("password/wrong-old"),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].error_messages["required"] = REQUIRED_MSG
        self.fields["new_password1"].error_messages["required"] = REQUIRED_MSG
        self.fields["new_password2"].error_messages["required"] = REQUIRED_MSG

    def validate_password_for_user(self, user, password_field_name="new_password2"):
        password = self.cleaned_data.get(password_field_name)
        if password:
            try:
                password_validation.validate_password(password, user)
            except forms.ValidationError as error:
                if error.error_list:
                    first_error = error.error_list[0]
                    code = first_error.code
                    if code == "password_too_short":
                        msg = get_error_message("password/too-short")
                    elif code == "password_too_common":
                        msg = get_error_message("password/too-common")
                    elif code == "password_entirely_numeric":
                        msg = get_error_message("password/numeric-only")
                    elif code == "password_too_similar":
                        msg = get_error_message("password/too-similar")
                    else:
                        msg = first_error.message
                    self.add_error(
                        "new_password1", forms.ValidationError(msg, code=code)
                    )


class RatingForm(forms.Form):
    """Form for submitting a service rating."""

    score = forms.ChoiceField(
        label="امتیاز",
        choices=[(str(i), str(i)) for i in range(1, 6)],
        error_messages={"required": "لطفاً یک امتیاز انتخاب کنید."},
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    comment = forms.CharField(
        label="نظر (اختیاری)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "نظر خود را درباره این خدمت بنویسید...",
            }
        ),
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


class OTPVerifyForm(forms.Form):
    """Form for entering the OTP code sent via SMS."""

    otp_code = forms.CharField(
        label="کد تأیید",
        max_length=6,
        min_length=6,
        error_messages={
            "required": REQUIRED_MSG,
            "max_length": "کد تأیید وارد شده نامعتبر است.",
            "min_length": "کد تأیید وارد شده نامعتبر است.",
        },
        widget=forms.TextInput(
            attrs={
                "class": "otp-input ltr-input",
                "placeholder": "۰۰۰۰۰۰",
                "dir": "ltr",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "pattern": "[0-9]{6}",
                "maxlength": "6",
            }
        ),
    )
