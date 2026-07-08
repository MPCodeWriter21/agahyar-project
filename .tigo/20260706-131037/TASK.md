# Download vendored static assets from CDN at Docker build time

- STATUS: CLOSED
- PRIORITY: 75
- TAGS: chore, vendoring
- DUE:

Replace the approach of committing vendored JS/CSS/font files to git with
downloading them from unpkg.com CDN at Docker build time (`vendor_static.sh`)
or on Windows (`vendor_static.ps1`).

Checkpoints:
- [x] Create scripts/vendor_static.sh (Linux/Docker) and scripts/vendor_static.ps1 (Windows)
- [x] Update Dockerfile to copy scripts/ and static/ early, run vendor_static.sh, then proceed
- [x] Mount only static/services/ in docker-compose.dev.yml (vendored files stay in image)
- [x] Add static/libs/ and static/Vazirmatn-Regular.woff2 to .gitignore
- [x] Remove all previously committed vendored files from git tracking with git rm --cached
- [x] Update AGENTS.md with the new vendoring convention
- [x] All 193 tests pass in Docker