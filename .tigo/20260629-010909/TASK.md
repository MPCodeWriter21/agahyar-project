# Increase test coverage

- STATUS: CLOSED
- PRIORITY: 70
- TAGS: testing, quality

Expand the test suite to cover edge cases and all code paths.

- Add tests for all view error paths (404, 500, permission denied)
- Add tests for edge cases (empty search, missing profile, etc.)
- Add form validation tests for all forms
- Add model method tests (get_documents_list, get_steps_list)
- Add integration tests for full user flows (register -> login -> search -> view detail -> logout)
- Add tests for scraper fallback logic
- Measure coverage with pytest-cov and aim for 80%+
