# Fix and complete user panel functionality

- STATUS: OPEN
- PRIORITY: 80
- TAGS: bug, ux, auth

The user panel (dashboard, profile, settings) is incomplete and has
buggy behavior. It needs to be fixed and expanded.

- Audit all user-facing views for bugs
- Add profile editing (change city, neighborhood, phone)
- Add password change form
- Add proper error handling for missing UserProfile
- Ensure all views gracefully handle users without a profile
- Add a proper user dashboard page (not just `show_users`)
- Add proper navigation for authenticated users
