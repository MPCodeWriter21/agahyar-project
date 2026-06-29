# Make contact-us and about pages public

- STATUS: CLOSED
- PRIORITY: 85
- TAGS: feature, auth

The contact-us and about pages must be accessible without login.

- Remove `login_required` / auth checks from the `about` and `contact` views
- Update templates to handle anonymous users gracefully
- Ensure the contact form POST works for anonymous users (no `request.user`)
- Update the ContactMessage model/creation to allow anonymous submissions
- Update tests that assert these pages require login
- Add tests for anonymous access to these pages
- Verify navigation links to these pages work for unauthenticated users
