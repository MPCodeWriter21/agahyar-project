# Dark/light theme support

- STATUS: CLOSED
- PRIORITY: 60
- TAGS: ux, frontend

Add per-device dark/light theme support using CSS custom properties and `prefers-color-scheme` media query (no DB storage).

- Define CSS custom properties for colors in both light and dark palettes
- Use `prefers-color-scheme: dark` media query for automatic switching
- Add a manual toggle button (sun/moon icon) in the header
- Store preference in `localStorage` for persistence across sessions
- Ensure all pages adopt the theme consistently
