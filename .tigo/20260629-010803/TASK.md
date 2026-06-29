# Fix logout and superuser inconsistencies

- STATUS: CLOSED
- PRIORITY: 85
- TAGS: bug, auth

Logging out from the user dashboard while logged in as a superuser
fails. There are inconsistencies between superuser and regular user
accounts that must be resolved.

- Fix the logout view/URL to work for all user types
- Ensure superusers can access the user dashboard without errors
- Ensure superuser profiles are handled correctly (UserProfile
  may not exist for superusers)
- Test all auth flows (login, logout, register, password reset)
  for both regular users and superusers
