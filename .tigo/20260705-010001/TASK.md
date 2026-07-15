# Implement ranked center suggestions

- STATUS: CLOSED
- PRIORITY: 50
TAGS: services, suggestion, ranking
DUE:

## Description

Implement smart service center suggestions with ranking in
`suggest_centers()` in `src/services/suggestion.py`. Currently downgraded
to returning only DB results or generic placeholders without any ranking.

## Checkpoints

- [ ] Define the ranking criteria (distance, rating, availability, user
  preferences)
- [ ] Implement scoring/ranking algorithm
- [ ] Integrate with `ServiceCenter` model data (coordinates, ratings, etc.)
- [ ] Return top-N suggestions with distance estimates
- [ ] Write/update tests for the new behavior
- [ ] Run full test suite to verify no regressions
