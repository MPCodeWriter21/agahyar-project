Development
===========

Prerequisites
-------------

- Python 3.12+
- `uv` (recommended)
- Git

Environment Variables
---------------------

Copy ``.env.example`` to ``.env`` and adjust the values for your environment:

```bash
cp .env.example .env
```

> **Note:** ``.env`` is git-ignored and must **not** be committed. Only
> ``.env.example`` (with placeholder values) is tracked.

> **Note:** The default ``.env.example`` sets up **PostgreSQL** (for Docker).
> If you are running **without Docker** (SQLite), comment out the PostgreSQL
> lines and uncomment the SQLite lines in ``.env``.

Setup (with uv -- recommended)
--------------------------------

Clone the repository and set up the environment:

```bash
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git
cd agahyar-project

# Create a virtual environment with uv
uv venv

# Install dependencies (from pyproject.toml)
uv sync

# (Optional) Install the project package in editable mode with dev extras
uv pip install -e ".[dev]"
```

Setup (without uv)
-------------------

If `uv` is not available, use standard `venv` + `pip`:

```bash
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git
cd agahyar-project

# Create a virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies (from pyproject.toml)
pip install -e ".[dev]"
```

Database
--------

Run migrations and create an admin user:

```bash
uv run migrate
uv run create-superuser
```

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

Development Server
------------------

```bash
uv run run-server
```

Then open <http://127.0.0.1:8000> in your browser.

Running Tests
-------------

```bash
uv run pytest
```

Populating Sample Data
----------------------

The repository includes scripts under ``scripts/`` to populate the database with
realistic sample data:

- ``populate_services.py`` -- creates (or updates) 9 government services and 34
  ServiceCenter records in a single run (idempotent, safe to re-run):

  ```bash
  uv run scripts/populate_services.py
  ```

- ``populate_faq.py`` -- creates (or updates) 30 FAQ entries covering all 9
  service categories plus general questions (idempotent):

  ```bash
  uv run scripts/populate_faq.py
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
