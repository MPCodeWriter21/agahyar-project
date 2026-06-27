# Consolidate inline CSS into a proper static CSS file
- STATUS: OPEN
- PRIORITY: 55
- TAGS: quality, ux

Each template has its own full-page <style> block duplicating many styles. Create a single style.css in static/ and include it via base.html.
