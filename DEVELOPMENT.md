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
├── src/                     # Python source packages
│   ├── agahyar_project/     # Django project configuration
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py / asgi.py
│   └── services/            # Main application
│       ├── models.py        # Service, UserProfile, FAQ, ServiceCenter
│       ├── views.py         # All view functions
│       ├── scraper.py       # Nearest-center logic and AI simulation
│       ├── urls.py          # App routes
│       ├── forms.py         # LoginForm, RegisterForm
│       ├── admin.py         # Admin panel registration
│       └── migrations/      # Database migrations
├── templates/
│   └── services/            # HTML templates
└── pyproject.toml           # Project metadata, dependencies, and tool config
```

Coding Conventions
------------------

- Python 3.12+ only
- Use `uv` for all Python commands (``uv run python ...``, ``uv run pytest``)
- Do not use ``python -c ...``; write a temporary script instead
- Docstrings follow reStructuredText (Sphinx) format
- Use ASCII only in source code -- avoid non-ASCII characters in .py files
