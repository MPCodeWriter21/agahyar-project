# Separate JS files + HTMX / Alpine.js / Datastar

- STATUS: CLOSED
- PRIORITY: 70
- TAGS: frontend, refactor

Move frontend logic from inline scripts to separate JS files. Evaluate and adopt a lightweight frontend framework.

- Extract all inline `<script>` blocks into separate `.js` files
- Consider using Alpine.js, Datastar, or HTMX for interactivity
- Add the chosen library via CDN or npm
- Remove any jQuery or heavy dependencies
- Update base template to load external JS files
- Add tests to verify JS files are served correctly (static file checks)
