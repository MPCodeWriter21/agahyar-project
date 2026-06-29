# Fix LTR field direction in RTL layout

- STATUS: CLOSED
- PRIORITY: 75
- TAGS: ux, bug, rtl

Fields that expect LTR input (username, email, password, phone) must use LTR text direction even when the page is RTL.

- Add `dir="ltr"` CSS class or inline attribute to these input fields
- Apply `text-align: left` and `direction: ltr` to affected fields
- Ensure the labels remain RTL aligned
- Check all forms: login, register, contact, profile, password change
- Add tests for HTML attribute presence in rendered forms
