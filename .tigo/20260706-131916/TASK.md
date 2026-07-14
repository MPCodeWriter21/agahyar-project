# Create GitHub Actions workflow to build and push Docker image on tag

- STATUS: CLOSED
- PRIORITY: 75
- TAGS: cd, ci, docker, release, workflow

Depends on: Task(20260706-131915)

Create a GitHub Actions workflow triggered on push that:
- Reads the version from the canonical source
- Check if a GitHub tg for that version already exists - if it already exists we do nothing
- Builds the Docker image
- Tags it with the version and `latest`
- Pushes to GHCR or Docker Hub

Checkpoints:
- [ ] Write the workflow YAML
- [ ] Test it end-to-end
