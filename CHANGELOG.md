# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.6.1] - 2026-07-23

### Fixed

- Removed Leaflet OpenStreetMap attribution text from maps
- Fixed maps not loading on page load (ReferenceError from `toPersianDigits` called before `main.js` defer script executed)
- Removed unnecessary `matomo-network` to fix intermittent 504 Gateway Timeout on Matomo dashboard
- Added `*.DOMAIN` to CSP `script-src` directive to allow Matomo analytics

## [1.6.0] - 2026-07-22

### Added

- **Comment reactions**: Like/dislike buttons on comments for both services
  and service centers. A new `CommentReaction` model tracks user reactions
  with unique constraints. The API exposes a `/react/` endpoint; the
  frontend updates counts in-place and highlights the user's active
  reaction.
- **Self-hosted Matomo analytics**: Added `docker-compose.matomo.yml` with
  Matomo 5 and MySQL 8.0 behind Traefik. Tracking snippet in `base.html`
  is conditionally rendered when `MATOMO_URL` and `MATOMO_SITE_ID` are set.
  A context processor supplies the values to templates.
- **Service description field**: New optional `description` TextField on the
  `Service` model. Rendered on the service detail page between the header
  and documents sections, hidden when empty. Supports multi-paragraph text.
- **Per-phone SMS rate limiting**: Cache-based limiter in `sms.py` blocks
  SMS sends to a single phone number after 5 messages per 10-minute window.
  Enforced inside `SMSClient.send_otp()` so all SMS paths are protected.
  The `resend_otp_api` and `resend_profile_otp_api` views now use
  `block=True` on the `@ratelimit` decorator.

### Changed

- **Service detail page hides empty fields**: Cost, duration, documents,
  and steps sections are now wrapped in `{% if %}` guards and are not
  rendered when the field is empty.
- **Pagination redesign**: Replaced prev/next-only pagination with numbered
  page buttons, ellipsis for distant pages, and a styled active-page
  indicator. Both `service_list.html` and `search.html` use semantic
  `<nav>` elements with `aria-label`.
- **Comment full name**: Comments now display the user's full name
  (first + last) instead of just the first name.
- **Alert replaced with toast notifications**: The native `alert()` call in
  the reaction error handler is replaced with a slide-up toast component
  (`showToast`). The existing `showReportSuccess` function now uses the
  same generic toast.
- **JS Unicode escapes decoded**: All escaped Persian/Arabic text in
  JavaScript files is now readable UTF-8. A garbled message in the
  geolocation error handler was corrected.
- **Admin data transfer import hardened**: Upload files larger than 10 MB
  or containing more than 10,000 records are rejected before reading into
  memory. `DATA_UPLOAD_MAX_MEMORY_SIZE` is set to 10 MB in settings.
- **Admin stats cached**: The admin dashboard view now caches aggregate
  queries for 5 minutes to avoid repeated full-table scans.
- **Sitemap memory-efficient**: Service and center querysets in the sitemap
  view now use `.iterator()` to avoid loading all objects into memory.
- **Comment reaction aggregation optimized**: The reaction counting loop
  in `service_detail` and `center_detail` now iterates through the prefetch
  cache once per comment instead of calling `.reactions.all()` three times.

### Fixed

- **Duplicate reaction requests on center detail page**: Removed a duplicate
  `main.js` include in `center_detail.html` that caused the delegated
  reaction click handler to fire twice, toggling the reaction back off.
- **SEO page titles**: Removed duplicated brand name from page titles.
  Base template now provides the default `<title>` with child templates
  supplying only the page-specific part.
- **Secrets management**: `SECRET_KEY` is required when `DEBUG=False`.
  System checks (`security.W001`/`W002`) validate security headers in
  production. Profiling middleware is gated on `DEBUG=True` and restricted
  to staff.
- **Access control**: `/users/` endpoint restricted to staff. API
  schema/docs views restricted to staff. Default DRF permission changed to
  `IsAuthenticated`. `PhoneVerification` removed from exportable models.
  Open redirect in password reset fixed with `|urlencode`.
- **Comment reaction frontend**: JS now checks `response.ok` before
  updating the UI. Reaction buttons on own comments are disabled in the
  template.

## [1.5.1] - 2026-07-22

### Fixed

- **Duplicate bookmark requests on service detail page**: Removed a duplicate
  `main.js` load in `service_detail.html` that caused the delegated bookmark
  click handler to fire twice per click, undoing the toggle.
- **OTP expiry tests**: Increased backdate from 10 to 30 minutes to match
  the new 20-minute `OTP_EXPIRE_MINUTES`.

## [1.5.0] - 2026-07-21

### Added

- **AJAX bookmark toggle**: Bookmark/unbookmark buttons on the home, services,
  search, dashboard, bookmarks, and service detail pages now use a delegated
  click handler that sends a POST via `fetch` in the background. The page no
  longer reloads when toggling a bookmark. On the bookmarks page, the card
  fades out and is removed from the DOM.
- **Tag list widget for admin**: A new `TagListWidget` for managing
  pipe/comma-separated list fields (documents, steps, keywords) in the admin
  panel. Supports add, remove, and drag-and-drop reorder with per-field
  configurable separator.
- **OTP security hardening**: Per-OTP brute-force counter
  (`PhoneVerification.failed_attempts`) blocks after 5 wrong attempts with an
  `otp/max-attempts` error. OTP expiry increased from 5 to 20 minutes
  (env-overridable via `OTP_EXPIRE_MINUTES`). Pending registration token TTL
  increased from 5 to 60 minutes. Session cookie age increased from 1 hour to
  6 hours.
- **OTP SMS delivery notice**: All OTP pages now advise users to wait up to 5
  minutes for SMS delivery due to potential carrier delays.

## [1.4.0] - 2026-07-21

### Added

- **City selector with search and lazy loading**: A searchable city dropdown
  backed by a new `/api/cities/` endpoint. Cities are ranked by service center
  count (top 20 shown by default), with AJAX search and infinite scroll for
  additional results. The `RegisterForm` and `ProfileForm` validate that the
  submitted city exists in the database.
- **Admin bulk data export/import**: A new admin page at `admin/data-transfer/`
  for exporting and importing all project data (services, centers, ratings,
  comments, etc.) as JSON. Supports dry-run mode, foreign key ordering, and
  M2M relationship handling. `ServiceCenterResource` now exports M2M services;
  a new `ServiceCenterPhoneResource` is available for phone number data.
- **Favicon with rounded hexagon design**: Added a custom favicon (teal
  `#1a5f7a` rounded hexagon with Persian letter "Alef") for the main site and
  a darker variant (`#0f3d52`) for the admin panel. A reusable generator
  script is at `scripts/generate_favicons.py`.
- **GitHub repository link**: Footer and about page now link to the GitHub
  repository with a Font Awesome icon.

### Changed

- **City dropdown overflows collapsible sections**: Changed `.collapsible-content`
  from `overflow: hidden` to `overflow: visible` so that the city selector
  dropdown can extend beyond the collapsed edit section.
- **Favicon generator is cross-platform**: The font path in
  `scripts/generate_favicons.py` now searches multiple OS-specific locations
  instead of hardcoding a Windows path. Pillow is declared as an optional
  dependency under `[project.optional-dependencies].scripts`.

### Fixed

- **OTP/registration test suite**: Added an `ensure_test_cities` pytest fixture
  that creates `ServiceCenter` records for cities used in tests. This fixes 28
  pre-existing test failures caused by `clean_city()` rejecting cities not
  present in the database.

## [1.3.0] - 2026-07-19

### Added

- **Login via phone number or email**: Users can now log in with their
  username, phone number, or email address. A custom authentication backend
  resolves the identifier across all three fields.
- **Username validation**: Registration now rejects all-numeric usernames and
  usernames containing the `@` character.
- **Service centers provide multiple services**: The `ServiceCenter.service`
  foreign key has been replaced with a `services` many-to-many field, allowing
  a single center to offer multiple government services.
- **Mailcow email integration**: Added `docker-compose.mailcow.yml` for
  self-hosted email via Mailcow (Postfix/Dovecot/Rspamd). Email settings in
  `settings.py` are now fully environment-driven. Created `MAIL_SETUP.md`
  with complete setup, DNS, and troubleshooting instructions.

### Changed

- **Email settings are environment-driven**: `EMAIL_BACKEND`, `EMAIL_HOST`,
  `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
  `DEFAULT_FROM_EMAIL`, and `SERVER_EMAIL` are now configurable via
  environment variables. The console backend remains the default for
  development.
- **Admin center list**: Shows comma-separated service names instead of a
  single service, with `filter_horizontal` widget for M2M editing.
- **API center serializer**: Exposes `service_names` (list) instead of
  `service_name` (single string).
- **Center detail page**: Displays all services a center provides with links,
  instead of a single service.
- **Login template**: Label and placeholder updated to indicate phone and
  email login support.

## [1.2.0] - 2026-07-18

### Changed

- **City-based center ordering**: The service detail page now orders
  centers with the user's profile city first (defaulting to Tehran for
  anonymous users), showing all centers available via "load more" instead
  of filtering to only the user's city.
- **Map syncs with loaded centers**: The service detail map now shows
  markers only for centers loaded in the list, adding markers as new
  pages are loaded via AJAX.

### Fixed

- **City name validation**: Cleaned up invalid city names in the SRA
  epishkhan data pipeline (street names, address fragments, province
  names no longer used as city names).

## [1.1.0] - 2026-07-18

### Added

- **Admin map widget with Neshan search**: The admin map widget now includes
  a search box powered by the Neshan API. Admins can search for locations and
  click to set latitude/longitude coordinates directly on the widget, with
  automatic sync between the map and coordinate inputs.
- **Multiple phone numbers per service center**: A new `ServiceCenterPhone`
  model allows each service center to have multiple phone numbers with labels
  (main, fax, mobile, other) and ordering. Phone numbers are displayed as
  clickable `tel:` links on the frontend using Persian digits.

### Fixed

- **CLI commands now use English**: The `LANGUAGE_CODE` has been changed from
  `fa` to `en-us`, with `LocaleMiddleware` added so that web requests still
  receive Persian via the browser's `Accept-Language` header. This ensures
  management commands like `createsuperuser` display English prompts and
  messages.
- **Docker Compose certResolver labels**: Added missing certResolver labels to
  the production Docker Compose configuration.
- **Test fix for Neshan search mock**: Added missing `close()` method to the
  mock `FP` object in the Neshan search proxy test to prevent
  `PytestUnraisableExceptionWarning`.
