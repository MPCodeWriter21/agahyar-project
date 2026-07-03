FROM astral/uv:python3.12-alpine AS builder

WORKDIR /app

# Copy application code
COPY pyproject.toml uv.lock manage.py ./
COPY src/agahyar_project ./src/agahyar_project
COPY src/services ./src/services

# Install project dependencies (including prod extras)
RUN uv sync --frozen --no-dev --extra prod
RUN uv pip install -e .

COPY static ./static
COPY templates ./templates

# minify static files
RUN apk add --no-cache minify
RUN if [[ -z "$DEBUG" ]]; then minify -air static; fi

# Collect static files into STATIC_ROOT
RUN uv run python manage.py collectstatic --noinput

# =====================================================================
FROM astral/uv:python3.12-alpine AS runtime

ENV TZ="Asia/Tehran"
WORKDIR /app

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
CMD uv run migrate \
    && uv run gunicorn agahyar_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --access-logfile - \
    --error-logfile -
