Development
===========

Prerequisites
-------------

- Python 3.12+
- `uv` (recommended) -- install from https://docs.astral.sh/uv/
- Git

Setup
-----

Clone the repository and set up the environment:

```bash
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git
cd agahyar-project

# Create a virtual environment with uv
uv venv

# Activate it
# Windows:
.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Install the project package in editable mode (with dev extras)
uv pip install -e ".[dev]"
```

Database
--------

Run migrations and create an admin user:

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

Development Server
------------------

```bash
uv run python manage.py runserver
```

Then open http://127.0.0.1:8000 in your browser.

Running Tests
-------------

```bash
uv run pytest
```

Project Structure
-----------------

```
agahyar-project/
├── agahyar_project/         # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
├── services/                # Main application
│   ├── models.py            # Service, UserProfile, FAQ, ServiceCenter
│   ├── views.py             # All view functions
│   ├── scraper.py           # Nearest-center logic and AI simulation
│   ├── urls.py              # App routes
│   ├── forms.py             # LoginForm, RegisterForm
│   ├── admin.py             # Admin panel registration
│   └── migrations/          # Database migrations
├── templates/
│   └── services/            # HTML templates
├── requirements.txt
└── pyproject.toml           # Project metadata and tool config
```

Coding Conventions
------------------

- Python 3.12+ only
- Use `uv` for all Python commands (``uv run python ...``, ``uv run pytest``)
- Do not use ``python -c ...``; write a temporary script instead
- Docstrings follow reStructuredText (Sphinx) format
- Use ASCII only in source code -- avoid non-ASCII characters in .py files
- Stage files explicitly (``git add file1 file2``), never ``git add -A`` or ``git add .``
