# Create pyproject.toml and migrate to uv build system
- STATUS: OPEN
- PRIORITY: 85
- TAGS: config, build

AGENTS.md mandates uv + pyproject.toml. The project currently uses only requirements.txt. Create pyproject.toml with project metadata, dependencies (from requirements.txt), and tool configuration for pytest and linting. Update DEVELOPMENT.md accordingly.
