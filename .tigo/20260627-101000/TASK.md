# Add phone number field to registration form
- STATUS: OPEN
- PRIORITY: 70
- TAGS: feature, auth

UserProfile has a phone field but save_user_profile_sql() never receives the phone parameter from registration. Add phone input to register form and pass it through.
