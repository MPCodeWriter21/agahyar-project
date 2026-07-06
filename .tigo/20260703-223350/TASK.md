# Improve website visual design

- STATUS: CLOSED
- PRIORITY: 55
- TAGS: ux, css, frontend

Polish the site's visual design, starting with form elements (especially select
boxes) and evaluating whether vendoring Tailwind CSS is worthwhile.

- Replace native `<select>` appearance with custom-styled selects across all
  contexts (form groups, filter/search rows): add a custom dropdown arrow,
  unify border-radius (currently 16px vs 40px), ensure dark mode and error
  state consistency, and improve the option menu styling
- Evaluate Tailwind CSS for this project: compare current 37KB custom CSS vs
  Tailwind's utility approach, check RTL support (`rtl:` modifier), dark mode
  integration, responsive breakpoint coverage, and vendoring cost (no CDN
  allowed)
- If Tailwind adds enough value: vendor it under `static/services/css/`,
  configure it (custom theme colors matching existing CSS variables), and
  progressively migrate templates to use utility classes
- If Tailwind does not add enough value: document the reasoning and instead
  consolidate the existing CSS (deduplicate near-identical button classes,
  unify form element styles, improve the select box custom styling)
