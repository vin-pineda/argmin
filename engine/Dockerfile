# syntax=docker/dockerfile:1
#
# Argmin engine — container image for any long-lived host (Fly.io / Render /
# Railway). The engine is too heavy for Vercel Python's 250 MB function limit
# (polars' Rust runtime + scipy/sklearn/cvxpy), so the API runs as a warm
# container and the Vercel web app proxies to it.
#
# Build context is `engine/`:  docker build -t argmin-engine engine/
#
# The package is run from source (PYTHONPATH=src), NOT pip-installed into
# site-packages, because argmin.config.engine_root() resolves config/ and the
# committed Parquet snapshot via __file__.parents[2] (the source layout).

FROM python:3.12-slim AS base

# uv for fast, reproducible installs from the committed lockfile.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/engine

# 1) Dependency layer — cached on (pyproject.toml, uv.lock). No project code yet,
#    no dev deps. This is the slow layer; it only rebuilds when deps change.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# 2) App code + the committed reproducibility snapshot (config + Parquet cache).
COPY src ./src
COPY config ./config
COPY data ./data

# Put the venv + source on the path; lock to production behavior. ARGMIN_DATA_DIR
# is absolute so cache resolution never depends on CWD. CORS origins are injected
# at deploy time (fly secrets / Render env) — default stays localhost for safety.
ENV PATH="/app/engine/.venv/bin:$PATH" \
    PYTHONPATH="/app/engine/src" \
    ARGMIN_ENV=production \
    ARGMIN_LOG_JSON=true \
    ARGMIN_DATA_DIR=/app/engine/data

# Container hosts route to this port; $PORT (Render/Railway) overrides at runtime.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn argmin.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
