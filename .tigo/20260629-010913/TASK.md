# Internationalization (i18n)

- STATUS: OPEN
- PRIORITY: 45
- TAGS: i18n

Add proper multi-language support using Django's i18n framework.

- Mark all user-facing strings with gettext / gettext_lazy
- Generate .po files for Persian (fa) and English (en)
- Translate all strings for both locales
- Add language switcher UI
- Ensure dates, times, and numbers are locale-aware
- Fall back to English when Persian translation is missing
