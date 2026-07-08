# Create GitHub Actions workflow to build and push Docker image on tag

- STATUS: OPEN
- PRIORITY: 75
- TAGS: cd, docker, release, workflow, ci

Parent: Task(20260706-131828)
Depends on: Task(20260706-131915)

Create a GitHub Actions workflow triggered on tag push (e.g. v*) that:
- Reads the version from the canonical source
- Builds the Docker image
- Tags it with the version and `latest`
- Pushes to GHCR or Docker Hub

Checkpoints:
- [ ] Write the workflow YAML
- [ ] Test it end-to-end