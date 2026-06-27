# Move SECRET_KEY to environment variables
- STATUS: OPEN
- PRIORITY: 100
- TAGS: security, critical

The Django SECRET_KEY is hardcoded in settings.py and exposed in the repository. Use python-decouple or django-environ to load it from a .env file.
