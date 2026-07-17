Deployment
==========

This document covers deployment for **local testing** and **production**.

Prerequisites
-------------

- Git
- Docker & Docker Compose

Environment Variables
---------------------

All configuration is driven by environment variables. Copy `.env.example` to `.env`
and adjust values:

```bash
cp .env.example .env
```

> **Critical production settings:**
>
> - `SECRET_KEY` -- generate a strong random key (`python -c "import secrets; print(secrets.token_urlsafe(50))"`)
> - `DEBUG=False`
> - `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
> - `SECURE_SSL_REDIRECT=True`
> - `SESSION_COOKIE_SECURE=True`
> - `CSRF_COOKIE_SECURE=True`
> - `SECURE_HSTS_SECONDS=31536000`
> - `SMS_IR_API_KEY=<your-sms-api-key>`
> - `SMS_IR_OTP_TEMPLATE_ID=<template-id>`
> - `DISABLE_SMS=False`

Local Deployment (for testing)
-------------------------------

### Docker Compose

```bash
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git
cd agahyar-project

cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

Open <http://localhost:8000>.

### Creating an Admin User

After migrating, create a superuser to access the admin panel:

```bash
docker compose -f docker-compose.dev.yml exec web uv run create-superuser
```

You will be prompted for a username, email, and password (in English, as
`LANGUAGE_CODE` is set to ``en-us``).

### Admin Panel

The Django admin panel is available at ``/admin/`` (e.g.
<http://127.0.0.1:8000/admin/>).

Log in with the superuser credentials created above. From the admin panel you
can manage:

- **Services** -- add, edit, or remove government services (name, organization,
  required documents, steps, cost, duration, keywords)
- **Service centers** -- assign physical locations to services (name, address,
  city, phone, coordinates)
- **FAQs** -- manage frequently asked questions with ordering
- **User profiles** -- view users' city, neighborhood, and phone number
- **Contact messages** -- read messages submitted via the contact form
  (read-only)

### Running Tests

```bash
docker compose -f docker-compose.dev.yml exec web uv run pytest
```

Production Deployment
---------------------

### Prerequisites

Before deploying with Docker Compose, create the Traefik network:

```bash
docker network create traefik-network
```

Also set up [traefik-starter](https://github.com/MPCodeWriter21/traefik-starter)
as a reverse proxy (or your own Traefik instance).

### Production Docker Compose

The project includes a production-ready `docker-compose.prod.yml` with PostgreSQL,
Redis, and Traefik labels for routing. The web service does **not** expose ports
directly -- Traefik handles HTTPS termination and routing.

You can either build locally or pull a pre-built image from GHCR:

```bash
# Build locally
docker compose -f docker-compose.prod.yml up --build -d

# Or pull from GHCR (replace with the correct image name for your fork)
VERSION=1.0.0
docker pull ghcr.io/fatemehmohammadganji/agahyar-project:$VERSION
```

Update `.env` for production:

```ini
SECRET_KEY=<generate-a-strong-random-key>
DEBUG=False
DOMAIN=yourdomain.com
SITE_URL=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
DB_ENGINE=django.contrib.gis.db.backends.postgis
DB_NAME=agahyar
DB_USER=agahyar
DB_PASSWORD=<strong-db-password>
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/1
SMS_IR_API_KEY=<your-sms-api-key>
SMS_IR_OTP_TEMPLATE_ID=<template-id>
DISABLE_SMS=False
OTP_EXPIRE_MINUTES=5
OTP_RESEND_COOLDOWN_SECONDS=60
```

After the containers are running, create the admin user:

```bash
docker compose -f docker-compose.prod.yml exec web uv run create-superuser
```

The application will be available at ``https://${DOMAIN}`` (where ``DOMAIN``
is set in your ``.env``).

> **Note:** A commented-out Adminer service is included in
> `docker-compose.prod.yml`. Uncomment it and set `ADMINER_DEFAULT_SERVER=db`
> to get a web-based database UI at <http://localhost:8080>.

> **Note:** The Dockerfile uses a multi-stage build. The first stage installs
> dependencies, minifies CSS/JS assets, and collects static files. The second
> (runtime) stage is a minimal image containing only what is needed to serve
> the application via Gunicorn.

Security Checklist
------------------

- [ ] `SECRET_KEY` is a strong random value, not the default
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` lists only your domains
- [ ] HTTPS is enforced (SSL redirect + HSTS)
- [ ] Database password is strong and not shared
- [ ] `.env` is **not** committed to the repository
- [ ] `SMS_IR_API_KEY` is set and valid
- [ ] `DISABLE_SMS=False` in production
- [ ] Regular database backups are configured

Data Management
---------------

### Seed Data

Sample services, service centers, and FAQs can be loaded with:

```bash
docker compose -f docker-compose.prod.yml exec web uv run scripts/populate_services.py
docker compose -f docker-compose.prod.yml exec web uv run scripts/populate_faq.py
```

Both scripts are idempotent -- running them multiple times updates existing
records rather than creating duplicates.

### Export and Import

Export all application data to JSON:

```bash
docker compose -f docker-compose.prod.yml exec web uv run manage.py export_data --output backup.json
```

Export to CSV:

```bash
docker compose -f docker-compose.prod.yml exec web uv run manage.py export_data --format csv --output backup.csv
```

Import from a JSON export:

```bash
docker compose -f docker-compose.prod.yml exec web uv run manage.py import_data backup.json
```

Preview an import without writing to the database:

```bash
docker compose -f docker-compose.prod.yml exec web uv run manage.py import_data backup.json --dry-run
```

### Database Backup

A backup script is provided in `scripts/backup_db.py`. It uses `pg_dump`
when available, and falls back to Django's `dumpdata` otherwise:

```bash
docker compose -f docker-compose.prod.yml exec web uv run scripts/backup_db.py
docker compose -f docker-compose.prod.yml exec web uv run scripts/backup_db.py --output-dir /path/to/backups
```

Backups are gzip-compressed and timestamped (e.g.
`backup_20260714_120000.sql.gz`).

### Restore

To restore from a `pg_dump` backup:

```bash
gunzip -c backups/backup_20260714_120000.sql.gz | psql -d agahyar
```

To restore from a `dumpdata` JSON backup:

```bash
docker compose -f docker-compose.prod.yml exec web uv run manage.py import_data backups/backup_20260714_120000.json.gz
```
