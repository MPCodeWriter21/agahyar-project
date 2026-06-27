# Fix password reset feature (uncomment and configure)
- STATUS: OPEN
- PRIORITY: 90
- TAGS: feature, auth

Password reset URL is commented out in urls.py. Templates exist under templates/registration/ but the route is disabled. Uncomment and configure email backend so users can reset passwords.
