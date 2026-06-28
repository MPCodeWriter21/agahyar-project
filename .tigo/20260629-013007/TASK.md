# Registration: first/last name, phone required, email optional

- STATUS: DONE
- PRIORITY: 80
- TAGS: feature, auth

Update registration to capture first and last names, make phone required, and email optional.

- Add `first_name` and `last_name` fields to RegisterForm
- Make `phone` required (remove `required=False`)
- Make `email` optional (`required=False`)
- Update the register template to show first/last name fields
- Update the register view to save first/last name on the User model
- Update UserProfile save logic for required phone
- Update tests for the changed form behavior
- Run all existing tests to confirm no regressions
