# Docker setup for production

- STATUS: CLOSED
- PRIORITY: 65
- TAGS: prod, docker

In production we should use technologies like PostgreSQL and Redis which should be present in the production compose file.
Also, we need a Dockerfile since some pre-processing should be done on some files before creating the docker image (e.g. minifying the CSS and JS assets).
