"""Error code catalog and Persian translation utilities.

Every user-facing error should be returned as a code; the frontend (or
this module) maps codes to Persian messages.
"""

ERROR_CODES: dict[str, str] = {
    # ---- Auth ----
    "auth/invalid-credentials": "نام کاربری یا رمز عبور اشتباه است.",
    "auth/login-required": "برای مشاهده این صفحه باید وارد شوید.",
    "auth/not-authorized": "شما مجوز دسترسی به این بخش را ندارید.",
    # ---- Generic validation ----
    "field/required": "وارد کردن این فیلد الزامی است.",
    "field/invalid-email": "ایمیل وارد شده معتبر نیست.",
    "field/max-length": "مقدار وارد شده بیش از حد مجاز است.",
    "field/min-length": "مقدار وارد شده کمتر از حد مجاز است.",
    "field/invalid-phone": "شماره تماس وارد شده معتبر نیست (مثال: 09121234567).",
    # ---- Password ----
    "password/mismatch": "رمز عبور و تکرار آن مطابقت ندارند.",
    "password/too-short": "رمز عبور باید حداقل ۸ کاراکتر باشد.",
    "password/too-common": "رمز عبور وارد شده خیلی ساده است.",
    "password/too-similar": "رمز عبور نمی‌تواند شبیه نام کاربری باشد.",
    "password/numeric-only": "رمز عبور نمی‌تواند فقط عدد باشد.",
    "password/wrong-old": "رمز عبور فعلی اشتباه است.",
    # ---- Username ----
    "username/duplicate": "این نام کاربری قبلاً ثبت شده است.",
    "username/required": "وارد کردن نام کاربری الزامی است.",
    # ---- Profile ----
    "profile/updated": "پروفایل شما با موفقیت به‌روزرسانی شد.",
    "password/changed": "رمز عبور شما با موفقیت تغییر یافت.",
    # ---- Contact ----
    "contact/sent": "پیام شما با موفقیت ارسال شد.",
    # ---- Register ----
    "register/welcome": "خوش آمدید {first_name}!",
    # ---- OTP ----
    "otp/sent": "کد تأیید به شماره موبایل شما ارسال شد.",
    "otp/invalid": "کد وارد شده اشتباه است.",
    "otp/expired": "کد تأیید منقضی شده است. لطفاً کد جدیدی دریافت کنید.",
    "otp/already-used": "این کد قبلاً استفاده شده است. لطفاً کد جدیدی دریافت کنید.",
    "otp/send-failed": "خطا در ارسال کد تأیید. لطفاً دوباره تلاش کنید.",
    "otp/too-many-resends": "تعداد درخواست‌های ارسال مجدد بیش از حد مجاز است. لطفاً چند دقیقه دیگر تلاش کنید.",
    "otp/no-pending-registration": "فرآیند ثبت‌نام منقضی شده است. لطفاً دوباره ثبت‌نام کنید.",
    "otp/resend-success": "کد جدید به شماره موبایل شما ارسال شد.",
    "otp/cooldown": "لطفاً {seconds} ثانیه دیگر صبر کنید.",
    # ---- Bookmark ----
    "bookmark/added": "خدمت مورد نظر به نشانک‌ها اضافه شد.",
    "bookmark/removed": "خدمت مورد نظر از نشانک‌ها حذف شد.",
    # ---- Comment ----
    "comment/added": "نظر شما با موفقیت ثبت شد.",
    "comment/updated": "نظر شما با موفقیت به‌روزرسانی شد.",
    "comment/deleted": "نظر شما با موفقیت حذف شد.",
    "comment/login-required": "برای ارسال نظر باید وارد شوید.",
    "comment/not-found": "نظر مورد نظر یافت نشد.",
    "comment/owner-only": "شما فقط می‌توانید نظر خود را ویرایش کنید.",
    "comment/edit-expired": "ویرایش نظر فقط تا ۲۴ ساعت پس از ارسال مجاز است.",
    "comment/cannot-reply-deleted": "امکان پاسخ به نظر حذف شده وجود ندارد.",
    "comment/cannot-edit-deleted": "امکان ویرایش نظر حذف شده وجود ندارد.",
    # ---- Center rating ----
    "center-rating/added": "امتیاز شما با موفقیت ثبت شد.",
    "center-rating/updated": "امتیاز شما با موفقیت به‌روزرسانی شد.",
    # ---- Geolocation ----
    "geolocation/unavailable": "امکان دریافت موقعیت جغرافیایی وجود ندارد.",
    "geolocation/invalid-coordinates": "مختصات وارد شده معتبر نیست.",
    # ---- Rate limiting ----
    "ratelimit/exceeded": "درخواست‌های زیادی ارسال کرده‌اید. لطفاً چند دقیقه دیگر تلاش کنید.",
    # ---- Uniqueness ----
    "email/duplicate": "این ایمیل قبلاً ثبت شده است.",
    "phone/duplicate": "این شماره تماس قبلاً ثبت شده است.",
}


def get_error_message(code: str, **kwargs: str) -> str:
    """Return the Persian message for *code*, optionally interpolating *kwargs*.

    :param code: An error code key from :data:`ERROR_CODES`.
    :param kwargs: Values to interpolate into the message template.
    :returns: The Persian message string (falls back to the code itself if unknown).
    """
    template = ERROR_CODES.get(code, code)
    if kwargs:
        return template.format(**kwargs)
    return template
