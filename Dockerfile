# syntax=docker/dockerfile:1

# ---- builder: resolve and install locked dependencies ----------------------------
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.17 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app

# Dependencies first (cached layer): only the manifest and the lockfile.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Then the project itself.
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- test: dev dependencies + tests, used by `make docker-test` ------------------
FROM builder AS test
COPY tests ./tests
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
CMD ["uv", "run", "--frozen", "pytest"]

# ---- runtime: the harness, non-root ----------------------------------------------
FROM python:3.12-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=builder /app /app
RUN groupadd --system app && useradd --system --gid app --uid 10001 --create-home app
USER 10001
CMD ["privilege-drift"]
