# Set up versioning strategy and centralize version source of truth

- STATUS: CLOSED
- PRIORITY: 75
- TAGS: enhancement, release, versioning

Parent: Task(20260706-131828)

Decide where the canonical version string lives (e.g. pyproject.toml
`[project] version`), document the convention, and ensure all downstream
consumers (Docker tags, GitHub releases, etc.) reference the same source.

Checkpoints:
- [ ] Choose version source of truth (one file — no duplication)
- [ ] Document the versioning scheme and version source in DEVELOPMENT.md
