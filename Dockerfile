FROM astral/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y curl libgdal-dev libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Download minify from GitHub releases: https://github.com/tdewolff/minify/releases/download/v2.24.13/minify_linux_amd64.tar.gz
# And extract it to /usr/local/bin
RUN ARCH="$(dpkg --print-architecture)" && \
    curl -fsSL \
      "https://github.com/tdewolff/minify/releases/download/v2.24.13/minify_linux_${ARCH}.tar.gz" \
    | tar -xz -C /usr/local/bin minify

# Install dev dependencies when INSTALL_DEV is set (non-empty)
ARG INSTALL_DEV=

COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --extra prod ${INSTALL_DEV:+--extra dev} --no-install-project

COPY manage.py ./
COPY src ./src

# Install the project itself
RUN uv pip install -e .

COPY static ./static
COPY templates ./templates

# minify static files
RUN minify -air static

COPY scripts ./scripts

# Collect static files into STATIC_ROOT
RUN uv run --no-sync python manage.py collectstatic --noinput

# =====================================================================
FROM astral/uv:python3.12-bookworm-slim AS runtime

ENV TZ="Asia/Tehran"
WORKDIR /app

RUN apt-get update && apt-get install -y libgdal-dev libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source, templates, static, and manage.py
COPY --from=builder /app/src /app/src
COPY --from=builder /app/templates /app/templates
COPY --from=builder /app/static /app/static
COPY --from=builder /app/staticfiles /app/staticfiles
COPY --from=builder /app/scripts /app/scripts
COPY --from=builder /app/manage.py /app/manage.py
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD uv run --no-sync python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Run migrations and start production server
CMD uv run --no-sync migrate \
    && uv run --no-sync gunicorn agahyar_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --access-logfile - \
    --error-logfile -
