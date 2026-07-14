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

Coding Conventions
------------------

- Python 3.12+ only
- Use `uv` for all Python commands (``uv run python ...``, ``uv run pytest``)
- Do not use ``python -c ...``; write a temporary script instead
- Docstrings follow reStructuredText (Sphinx) format
- Use ASCII only in source code -- avoid non-ASCII characters in .py files
