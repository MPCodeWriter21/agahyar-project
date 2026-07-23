# Security: Fix SMS cost amplification vulnerabilities

- STATUS: CLOSED
- PRIORITY: 90
- TAGS: security, sms, cost-amplification, high

Security audit found critical SMS cost amplification vulnerabilities that allow attackers to cause significant financial damage.

== VULN-07 (HIGH): SMS Cost Amplification via API Resend OTP ==
File: src/services/views.py, lines 296-365 (resend_otp_api); lines 458-517 (resend_profile_otp_api)
Both resend_otp_api and resend_profile_otp_api use @ratelimit with block=False. The rate limit is checked but the request proceeds regardless. An attacker can flood these endpoints to trigger massive SMS sends.
Fix: Change block=False to block=True for the resend API endpoints. Additionally, add per-phone number rate limiting (not just per-IP).

== VULN-08 (MEDIUM): SMS Sent Without Verifying Registration Status ==
File: src/services/views.py, lines 255-293 (resend_otp_view)
The same phone number from different IPs (or cleared cookies) can trigger fresh OTP sends repeatedly.
Fix: Add per-phone-number rate limiting at the SMS sending layer.

== VULN-09 (HIGH): No Per-Phone SMS Rate Limiting ==
File: src/services/views.py (all OTP-related views), src/services/auth_api.py (all auth views)
All SMS-sending operations rate-limit by IP or user, but never by phone number. An attacker using a proxy rotation service can send thousands of SMS messages to any phone number.
Fix: Add a per-phone rate limiter (using cache keyed by phone number) at the SMS client level.
