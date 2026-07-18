# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
