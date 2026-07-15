Development
===========

Prerequisites
-------------

- Git
- Docker & Docker Compose

Environment Variables
---------------------

Copy ``.env.example`` to ``.env`` and adjust the values for your environment:

```bash
cp .env.example .env
```

> **Note:** ``.env`` is git-ignored and must **not** be committed. Only
> ``.env.example`` (with placeholder values) is tracked.

> **Note:** This project uses **PostGIS** (PostgreSQL with spatial extensions)
> and is designed to run via Docker. Local (non-Docker) development is not
> supported.

> **Note:** SMS phone verification (OTP) is enabled by default. In
> development, set ``DISABLE_SMS=True`` in your ``.env`` to skip sending
> actual SMS messages -- OTP codes will be printed to the container console
> instead.

Docker
------

### Development

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

The application will be available at <http://localhost:8000>.

[Adminer](https://www.adminer.org/) is also available at
<http://localhost:8080> for database management. Select **PostgreSQL** as the
driver, enter the credentials from ``.env``, and leave the server as ``db``.

### Production

```bash
# Adjust .env for production (postgres, redis, etc.)
docker compose -f docker-compose.prod.yml up --build -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full production instructions.

Running Commands Inside the Container
-------------------------------------

All development commands (migrate, tests, scripts) run inside the web container:

```bash
# Run migrations
docker compose -f docker-compose.dev.yml exec web uv run migrate

# Create a superuser
docker compose -f docker-compose.dev.yml exec web uv run create-superuser

# Run tests
docker compose -f docker-compose.dev.yml exec web uv run pytest

# Populate sample data
docker compose -f docker-compose.dev.yml exec web uv run scripts/populate_services.py
docker compose -f docker-compose.dev.yml exec web uv run scripts/populate_faq.py
```

Project Structure
-----------------

```
agahyar-project/
├── src/                          # Python source packages
│   ├── agahyar_project/          # Django project configuration
│   │   ├── __init__.py
│   │   ├── asgi.py               # ASGI entry point
│   │   ├── middleware.py          # SecurityHeadersMiddleware
│   │   ├── scripts.py            # Console-script entry points
│   │   ├── settings.py           # Django settings
│   │   ├── urls.py               # Root URL config + 429 handler
│   │   └── wsgi.py               # WSGI entry point
│   └── services/                 # Main application
│       ├── __init__.py
│       ├── admin.py              # Admin panel registration
│       ├── apps.py               # Django AppConfig
│       ├── error_codes.py        # Persian error code catalog
│       ├── forms.py              # LoginForm, RegisterForm, OTPVerifyForm, etc.
│       ├── models.py             # Service, UserProfile, FAQ, PhoneVerification, etc.
│       ├── otp.py                # OTP generation, hashing, and verification
│       ├── sms.py                # SMS.ir API client for sending OTP codes
│       ├── suggestion.py         # Nearest-center lookup logic
│       ├── urls.py               # App URL patterns
│       ├── validators.py         # Iranian phone & password validators
│       ├── views.py              # All view functions
│       ├── migrations/           # Database migrations
│       └── test_*.py             # Pytest test files
├── scripts/                      # Data population scripts
│   ├── populate_services.py
│   └── populate_faq.py
├── templates/
│   └── services/                 # HTML templates
├── static/
│   └── services/                 # CSS, JS, fonts, icons (no CDN)
├── Dockerfile                    # Multi-stage build
├── docker-compose.dev.yml        # Dev compose (PostGIS + Redis + Adminer)
├── docker-compose.prod.yml       # Prod compose (Traefik, Gunicorn)
├── pyproject.toml                # Project metadata, dependencies, tooling
├── .env.example                  # Environment variable template
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml
├── README.md
├── DEVELOPMENT.md
├── DEPLOYMENT.md
└── AGENTS.md
```

Caching
-------

Django's caching framework is always active:

- **With Redis** (``REDIS_URL`` set): Redis is used as the cache backend.
  Sessions are also stored in the cache.
- **Without Redis** (``REDIS_URL`` unset or commented): ``LocMemCache``
  (in-memory, per-process) is used as a fallback.  This is suitable for
  local development but does not share state across workers or containers.

Template fragments use ``{% cache %}`` for expensive or rarely-changing
content (e.g. FAQ lists).  The default TTL is 900 seconds (15 minutes).
Cache keys include a version suffix so they are invalidated automatically
when the underlying data changes.

GZip compression is enabled via ``django.middleware.gzip.GZipMiddleware``
in all environments.

Session Management
------------------

Sessions use a *sliding window* approach.  The ``SessionRefreshMiddleware``
resets the session expiry on every authenticated request, so active users
stay logged in as long as they keep using the site.  Inactive users are
logged out after ``SESSION_COOKIE_AGE`` seconds (default: 3600).

Key settings (in ``settings.py``):

- ``SESSION_COOKIE_AGE`` -- inactivity timeout in seconds (default: 3600)
- ``SESSION_EXPIRE_AT_BROWSER_CLOSE`` -- cookie expires when the browser
  closes (always ``True``)
- ``SESSION_ENGINE`` -- cache-backed when Redis is available, otherwise
  the default database backend

Profiling
---------

A per-request profiling middleware is available for diagnosing performance
bottlenecks.  It uses Python's ``cProfile`` and adds query-count headers
to every response.

### Enabling

Set the ``ENABLE_PROFILING`` environment variable:

```bash
# In .env
ENABLE_PROFILING=True
```

Recreate the container for the change to take effect (``docker compose -f
docker-compose.dev.yml up -d``

### Usage

1. Make a request to any page.
2. Check the response headers:
   - ``X-Profile-Queries``: number of SQL queries executed during the
     request.
3. To see the full cProfile report, append ``?profile=1`` to any HTML
   page URL.  A dark-themed table is appended to the page showing the
   top 50 functions sorted by cumulative time.

### Reading the report

The report shows per-function statistics:

- **ncalls**: how many times the function was called
- **tottime**: total time spent in the function (excluding sub-calls)
- **cumtime**: cumulative time including sub-calls
- **filename:lineno**: source location

Focus on functions with high ``cumtime`` -- these are the bottlenecks.

### Example

```bash
# Enable profiling
echo "ENABLE_PROFILING=True" >> .env
docker compose -f docker-compose.dev.yml up -d

# View profiled page
open "http://localhost:8000/service/1/?profile=1"
```

Monitoring and Logging
----------------------

### Health Check

The ``/health/`` endpoint is a lightweight health check for uptime
monitors and load balancers.  It verifies database connectivity and
returns a simple JSON response:

```json
{"status": "ok", "version": "0.1.0", "database": "ok"}
```

Returns HTTP 200 when healthy, 503 when degraded.

### Server Status (Admin Only)

The ``/admin/server-status/`` endpoint exposes detailed server resource
information.  Access is restricted to staff users.  Returns:

- ``cpu_percent`` -- current CPU usage
- ``memory_rss_mb`` -- resident memory in MB
- ``memory_percent`` -- memory usage as percentage
- ``disk_percent`` -- disk usage as percentage
- ``database`` -- database connectivity status

### Request IDs

Every request receives a unique UUID4 identifier.  The ID is:

- Returned in the ``X-Request-ID`` response header
- Included in all log entries produced during the request
- Forwarded from clients if the ``X-Request-ID`` header is already
  present in the request

### Structured Logging

Logs use a verbose format with request context:

```
2026-07-15 12:00:00 INFO [django.request] [req:abc-123] views:42 GET /faq/ 200
```

Log files are stored under ``logs/`` in the project root:

- ``logs/django.log`` -- all logs (INFO and above)
- ``logs/error.log`` -- errors only

Both files use ``RotatingFileHandler`` with a 10 MB size limit and 5
backup files.

### Sentry Error Tracking

Sentry integration is available for production error tracking.  Set the
``SENTRY_DSN`` environment variable to enable:

```bash
SENTRY_DSN=https://your-key@sentry.io/project-id
```

When enabled, Sentry captures unhandled exceptions with 10% trace
sampling.  The environment tag (``development`` / ``production``) is
derived from the ``DEBUG`` setting.

Coding Conventions
------------------

- Python 3.12+ only
- Use `uv` for all Python commands (``uv run python ...``, ``uv run pytest``)
- Do not use ``python -c ...``; write a temporary script instead
- Docstrings follow reStructuredText (Sphinx) format
- Use ASCII only in source code -- avoid non-ASCII characters in .py files

Versioning
----------

The project version is defined in a single place: the ``version`` field
under ``[project]`` in ``pyproject.toml``. This is the canonical source of
truth -- do not duplicate the version string in any other file.

At runtime, the version is accessible via ``agahyar_project.__version__``,
which reads from ``importlib.metadata`` (so it always reflects the installed
package version without duplication).

Docker images receive the version at build time through a ``VERSION`` build
arg, which is set to the ``org.opencontainers.image.version`` OCI label.

To bump the version, edit only the ``version`` field in ``pyproject.toml``
and run ``uv lock`` to update the lockfile.

Release Workflow
----------------

The ``release.yml`` GitHub Actions workflow automates Docker image releases.
On every push to ``main``, it:

1. Reads the version from ``pyproject.toml``.
2. Checks if a Git tag ``v<version>`` already exists.
3. If the tag exists, the workflow exits early (already released).
4. If the tag does not exist, it builds the Docker image, pushes it to
   GHCR (``ghcr.io/<owner>/<repo>``), creates the Git tag, and publishes
   a GitHub Release with auto-generated notes.

The image name is derived from ``${{ github.repository }}``, so forks
automatically release images under their own GHCR namespace.

To release a new version, simply bump the version in ``pyproject.toml``,
push to ``main``, and the workflow handles the rest.
