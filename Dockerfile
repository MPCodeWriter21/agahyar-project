# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install project dependencies (including prod extras)
RUN uv sync --frozen --no-dev --extra prod

# Copy application code
COPY . .

# Minify CSS and JS assets (production build step)
RUN uv pip install cssmin jsmin --no-deps \
    && python -c "\
import cssmin; \
f = 'static/services/css/style.css'; \
open(f, 'w', encoding='utf-8').write(cssmin.cssmin(open(f, encoding='utf-8').read())) \
" \
    && python -c "\
import jsmin; \
for f in ['static/services/js/main.js', 'static/services/js/error-translate.js']: \
    open(f, 'w', encoding='utf-8').write(jsmin.jsmin(open(f, encoding='utf-8').read())) \
" \
    && uv pip uninstall cssmin jsmin -y

# Collect static files into STATIC_ROOT
RUN uv run python manage.py collectstatic --noinput

# =====================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime system deps (only libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary (used for create-superuser command)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source, templates, static, and manage.py
COPY --from=builder /app/src /app/src
COPY --from=builder /app/templates /app/templates
COPY --from=builder /app/static /app/static
COPY --from=builder /app/staticfiles /app/staticfiles
COPY --from=builder /app/manage.py /app/manage.py
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Run migrations and start production server
CMD uv run python manage.py migrate \
    && uv run gunicorn agahyar_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --access-logfile - \
    --error-logfile -
