# Implement passport info scraper

STATUS: PENDING
PRIORITY: LOW
TAGS: services, scraper, passport
DUE:

## Description

Implement real external data scraping for passport information in
`scrape_passport_info()` in `src/services/suggestion.py`. Currently
downgraded to returning hardcoded fallback data.

## Checkpoints

- [ ] Identify reliable official sources for passport fee/processing info
  (e.g. police.ir, passport.ir)
- [ ] Implement proper HTML parsing with error handling
- [ ] Add caching to avoid excessive requests
- [ ] Write/update tests for the new behavior
- [ ] Run full test suite to verify no regressions
