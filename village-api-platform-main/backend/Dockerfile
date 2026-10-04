FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install uv from PyPI (fast wheel) instead of pulling a large ghcr.io image,
# which is slow/throttled on some networks. All runtime deps ship binary
# wheels, so no system compiler packages are required.
RUN pip install --no-cache-dir uv

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies (no dev tools). The uv cache is mounted so a
# flaky/slow PyPI retries resume rather than restarting downloads.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]