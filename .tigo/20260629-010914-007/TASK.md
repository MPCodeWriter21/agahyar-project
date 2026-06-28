# Security hardening

- STATUS: OPEN
- PRIORITY: 85
- TAGS: security

Harden the application against common web vulnerabilities.

- Add rate limiting on login and contact forms
- Add request throttling (django-ratelimit or similar)
- Audit all forms for CSRF protection
- Sanitize user inputs in search and contact forms
- Set session expiry and cookie age limits
- Add Content-Security-Policy headers
- Run bandit security linter and fix findings
- Ensure admin panel is not exposed on a predictable URL
