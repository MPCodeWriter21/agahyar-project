# Security: Fix secrets management and security configuration

- STATUS: CLOSED
- PRIORITY: 92
- TAGS: security, secrets, configuration, critical

Security audit found critical issues with secrets management and security configuration that could allow session forgery, credential theft, or security bypass.

== VULN-18 (CRITICAL): Hardcoded Insecure SECRET_KEY Fallback ==
File: src/agahyar_project/settings.py, line 29
SECRET_KEY falls back to a known insecure default if not set via environment variable. If the .env file is missing or misconfigured in production, the application runs with a known secret key, allowing session cookie forgery, CSRF token forgery, and signed data manipulation.
Fix: Remove the default or raise an error if SECRET_KEY is not set. Never use a hardcoded fallback.

== VULN-20 (HIGH): Security Headers Disabled by Default ==
File: src/agahyar_project/settings.py, lines 40-47
SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, and SECURE_HSTS_SECONDS all default to False/0. In production, if these are not explicitly set, the application sends cookies over HTTP and is vulnerable to SSL stripping.
Fix: Default these to True/non-zero for production. Add startup validation that rejects insecure configurations when DEBUG=False.

== VULN-21 (MEDIUM): Profiling Middleware Leaks Internal Information ==
File: src/agahyar_project/middleware.py, lines 33-131
When ENABLE_PROFILING=True, ProfilingMiddleware appends full cProfile report to HTML responses, exposing internal file paths, function names, SQL query counts, and execution times.
Fix: Restrict profiling to DEBUG=True only, or require staff authentication. Never enable in production.
