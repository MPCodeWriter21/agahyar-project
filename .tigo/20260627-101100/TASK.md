# Add input validation for Iranian phone numbers
- STATUS: CLOSED
- PRIORITY: 70
- TAGS: quality, validation

UserProfile.phone is CharField(max_length=11) with no validator. Add a validator ensuring format starts with 09 and has 11 digits.
