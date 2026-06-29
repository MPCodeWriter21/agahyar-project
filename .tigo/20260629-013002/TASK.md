# Form validation without reset

- STATUS: CLOSED
- PRIORITY: 80
- TAGS: ux, bug

When form validation fails, the form must NOT reset its values. It must preserve entered values and highlight failed fields.

- Audit all forms (login, register, contact, profile, password change)
- Ensure Django forms re-render with bound data on validation failure
- Add visual field-level error highlighting (red border, inline message)
- Add tests for form re-rendering behavior
