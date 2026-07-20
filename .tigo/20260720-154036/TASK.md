# City selector: search, top-20 by center count, lazy loading

- STATUS: OPEN
- PRIORITY: 50
- TAGS: frontend, backend, ux
- DUE: 2026-07-25

## Description

The city selector in registration and profile pages currently sends all cities
to the client at once. This is inefficient when there are many cities. We need
to show only the top 20 cities (by number of registered service centers) by
default, with search and load-more for the rest.

### Requirements

1. Only the first 20 cities should be shown by default, ordered by number of
   registered service centers (descending).
2. The city selector must have a search input so less popular cities can be
   found.
3. In the profile page, the user's currently selected city must always be
   available even if it is not in the top 20.
4. Other cities (not top 20 and not selected) can be searched for or loaded
   via a "load more" button at the bottom of the select dropdown.
5. Not all cities must be sent to the client at once since they may be many.
6. Use and improve the existing custom select component.

### Checkpoints

- [x] Create `/api/cities/` backend endpoint with search, pagination, and
      center count annotation
- [x] Update `get_city_choices()` to `get_top_city_choices(limit=20)` in forms.py
- [x] Update `RegisterForm` and `ProfileForm` to use top-20 choices
- [x] Add `clean_city()` validation to accept lazy-loaded cities
- [x] Update `register_view` and `profile_view` to pass new choices
- [x] Add `data-searchable` and `data-api-url` attributes to city `<select>` in
      register.html, profile.html, and search.html
- [x] Enhance `custom-select.js` with search input, AJAX loading, and load-more
      button
- [x] Add CSS styles for search input and load-more button in custom select
- [x] Add tests for the new API endpoint
- [x] Update existing tests for `get_top_city_choices`
- [x] Add tests for profile form including user's city
- [x] Run full test suite and lint
