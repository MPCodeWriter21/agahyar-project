# Configure DEBUG and ALLOWED_HOSTS for production
- STATUS: OPEN
- PRIORITY: 100
- TAGS: security, critical

DEBUG is set to True and ALLOWED_HOSTS is empty. Add SECURE_* settings, set DEBUG=False, configure ALLOWED_HOSTS, and add HTTPS/SSL settings.
