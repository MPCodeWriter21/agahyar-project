# Use Django form validation for login
- STATUS: OPEN
- PRIORITY: 75
- TAGS: quality, refactor

Login view extracts POST data directly (request.POST.get()). The LoginForm class exists in forms.py but is never used for POST validation. Use form.is_valid() pattern.
