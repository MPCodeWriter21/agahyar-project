Deployment
==========

This document covers deployment for **local testing** and **production**.

Prerequisites
-------------

- Python 3.12+
- Git
- Docker & Docker Compose (optional, for containerized deployment)
- PostgreSQL (optional, for production)

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

Local Deployment (for testing)
-------------------------------

### Option A: uv (recommended)

```bash
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git
cd agahyar-project

cp .env.example .env
uv venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

uv sync
uv pip install -e ".[dev]"

uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Open http://127.0.0.1:8000.

### Option B: pip (without uv)

```bash
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git
cd agahyar-project

cp .env.example .env
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -e ".[dev]"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Option C: Docker Compose

```bash
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git
cd agahyar-project

cp .env.example .env
docker compose up --build
```

Open http://127.0.0.1:8000.

### Creating an Admin User

After migrating, create a superuser to access the admin panel:

```bash
uv run python manage.py createsuperuser    # with uv
# or
python manage.py createsuperuser           # without uv
```

For Docker Compose (non-production), run it inside the running container:

```bash
docker compose exec web uv run python manage.py createsuperuser
```

You will be prompted for a username, email, and password (in English, as
`LANGUAGE_CODE` is set to ``en-us``).

### Admin Panel

The Django admin panel is available at ``/admin/`` (e.g.
http://127.0.0.1:8000/admin/).

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
uv run pytest          # with uv
# or
pytest                 # with plain pip
```

Production Deployment
---------------------

### Production Docker Compose

Create a `docker-compose.prod.yml`:

```yaml
services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: agahyar
      POSTGRES_USER: agahyar
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: unless-stopped

  web:
    build:
      context: .
      dockerfile: Dockerfile
    command: >
      sh -c "uv run python manage.py migrate
      && uv run python manage.py collectstatic --noinput
      && uv run gunicorn agahyar_project.wsgi:application --bind 0.0.0.0:8000"
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    restart: unless-stopped

volumes:
  postgres_data:
```

Update `.env` for production:

```ini
SECRET_KEY=<generate-a-strong-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=agahyar
DB_USER=agahyar
DB_PASSWORD=<strong-db-password>
DB_HOST=db
DB_PORT=5432
```

Then deploy:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

After the containers are running, create the admin user:

```bash
docker compose -f docker-compose.prod.yml exec web uv run python manage.py createsuperuser
```

### Manual Deployment (bare metal / VPS)

1. Clone and set up the project (see Local Deployment above).
2. Install and configure PostgreSQL, then set `DB_ENGINE`, `DB_NAME`, `DB_USER`,
   `DB_PASSWORD`, `DB_HOST`, `DB_PORT` in `.env`.
3. Install a production WSGI server:

   ```bash
   pip install gunicorn
   ```

4. Collect static files:

   ```bash
   python manage.py collectstatic --noinput
   ```

5. Run with Gunicorn:

   ```bash
   gunicorn agahyar_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
   ```

6. Create the admin superuser:

   ```bash
   python manage.py createsuperuser
   ```

7. Set up a reverse proxy (nginx / Caddy) in front of Gunicorn to handle
   SSL termination and static file serving.

The admin panel is then available at ``https://yourdomain.com/admin/``.

### Static and Media Files

In production, configure your reverse proxy to serve:

- `STATIC_URL` (`/static/`) from `<project-root>/staticfiles/` (created by `collectstatic`)
- `MEDIA_URL` (`/media/`) from `<project-root>/media/`

Example nginx snippet:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/agahyar-project/staticfiles/;
    }

    location /media/ {
        alias /path/to/agahyar-project/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Security Checklist
------------------

- [ ] `SECRET_KEY` is a strong random value, not the default
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` lists only your domains
- [ ] HTTPS is enforced (SSL redirect + HSTS)
- [ ] Database password is strong and not shared
- [ ] `.env` is **not** committed to the repository
- [ ] Regular database backups are configured
