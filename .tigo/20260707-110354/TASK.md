# The users must verify their phone number before they're registered

- STATUS: CLOSED
- PRIORITY: 70
- TAGS: sms, auth, feature, register, verification

We will use sms.ir API: https://sms.ir/rest-api/
The code will be 6 digits.
The code will always be printed to the backend console.
Sending the SMS via API can be enabled/disabled with a flag in `.env`. When it's disabled, the admin can look through the logs in the backend console for the code.
The implementation and usage must be documented properly.
