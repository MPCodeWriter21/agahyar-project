# Replace raw SQL with Django ORM
- STATUS: CLOSED
- PRIORITY: 80
- TAGS: quality, refactor

save_user_profile_sql() in views.py uses raw SQL INSERT with string formatting. Replace with UserProfile.objects.update_or_create() for consistency and maintainability.
