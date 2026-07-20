# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
