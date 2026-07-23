# Security: Fix access control & data exposure vulnerabilities

- STATUS: CLOSED
- PRIORITY: 95
- TAGS: security, access-control, data-exposure, critical

Security audit found critical access control and data exposure vulnerabilities that must be fixed immediately.

== VULN-01 (HIGH): User PII Exposed to All Authenticated Users ==
File: src/services/views.py, lines 1149-1164
URL: /users/
The show_users view is accessible to any logged-in user and returns full user list including ID, username, email, city, and PHONE NUMBER of every registered user.
Fix: Remove this view entirely or restrict to @staff_member_required. If a user directory is needed, exclude sensitive fields (phone, email).

== VULN-02 (MEDIUM): API Schema Exposed Without Authentication ==
File: src/services/api_urls.py, lines 38-43
URL: /api/v1/schema/ and /api/v1/docs/
The OpenAPI schema and Swagger UI are publicly accessible, exposing every API endpoint, parameters, auth requirements, and data models.
Fix: Restrict /api/v1/schema/ and /api/v1/docs/ to staff-only in production.

== VULN-05 (MEDIUM): Default DRF Permission is AllowAny ==
File: src/agahyar_project/settings.py, lines 353-355
Global DRF DEFAULT_PERMISSION_CLASSES is set to AllowAny. Any new ViewSet added without explicit permission classes will be publicly accessible.
Fix: Change DEFAULT_PERMISSION_CLASSES to IsAuthenticated and add AllowAny explicitly where needed.

== VULN-03 (LOW): PhoneVerification Data in Exportable Models ==
File: src/services/views.py, lines 2127-2138
PhoneVerification is listed in EXPORTABLE_MODELS for admin data transfer. OTP data including phone numbers should not be exportable.
Fix: Remove PhoneVerification from EXPORTABLE_MODELS.

== VULN-06 (LOW): Open Redirect via next Parameter ==
File: templates/services/service_detail.html, lines 198-201
Login/register links include ?next={{ request.path }} directly from request path.
Fix: Use {{ request.path|urlencode }} to properly encode the path.
