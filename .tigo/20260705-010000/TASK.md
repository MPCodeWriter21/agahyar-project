# Implement proximity-based nearest center lookup

STATUS: PENDING
PRIORITY: MEDIUM
TAGS: services, suggestion, location
DUE:

## Description

Implement real proximity-based nearest center lookup in `get_nearest_center()`
in `src/services/suggestion.py`. Currently downgraded to always returning
None, causing views to fall back to a simple city-filtered DB query.

## Checkpoints

- [ ] Choose a strategy: geospatial DB query (PostGIS), coordinate distance
  calculation, or neighborhood-based mapping
- [ ] Ensure the `ServiceCenter` model has usable location data (coordinate
  field or address for geocoding)
- [ ] Implement the lookup to return the closest `ServiceCenter` for a given
  service, city, and neighborhood
- [ ] Write/update tests for the new behavior
- [ ] Run full test suite to verify no regressions
