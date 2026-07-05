/**
 * Agahyar - Error code translation
 *
 * Maps backend error codes to Persian messages for client-side use.
 */

window.AgahyarErrors = {
  "field/required": "وارد کردن این فیلد الزامی است.",
  "field/invalid-email": "ایمیل وارد شده معتبر نیست.",
  "field/invalid-phone": "شماره تماس وارد شده معتبر نیست (مثال: 09121234567).",
  "password/mismatch": "رمز عبور و تکرار آن مطابقت ندارند.",
  "password/too-short": "رمز عبور باید حداقل 8 کاراکتر باشد.",
  "auth/invalid-credentials": "نام کاربری یا رمز عبور اشتباه است.",
};

window.translateError = function (code) {
  return window.AgahyarErrors[code] || code;
};
