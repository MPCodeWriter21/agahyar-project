# Persian error translation layer

- STATUS: CLOSED
- PRIORITY: 85
- TAGS: ux, i18n, refactor

Implement error code based translation layer so all frontend error messages are in Persian.

- Define an error code catalog on the backend (return codes instead of raw messages)
- Create a frontend JS module that maps error codes to Persian messages
- Update all views to return error codes
- Ensure login, register, profile, contact forms use the translation layer
- Add tests for error code mapping
- Remove any hardcoded English error strings from templates
