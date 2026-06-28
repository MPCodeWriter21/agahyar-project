# Host Vazirmatn font locally

- STATUS: OPEN
- PRIORITY: 75
- TAGS: design, font, asset

Vazirmatn is the preferred Persian font. It must be hosted locally
(no CDN) inside the project's static files.

- Download Vazirmatn font files (woff2)
- Place them under `static/services/fonts/vazirmatn/`
- Create a CSS file (or update existing) that declares the `@font-face`
- Apply the font to the `body` in `base.html`
- Remove any external font/CDN dependencies
