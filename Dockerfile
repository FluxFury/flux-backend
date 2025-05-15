FROM python:3.12-slim-bullseye

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    APP_MODULE="flux_backend.main:app" \
    APP_HOST="0.0.0.0" \
    APP_PORT="8000" \
    PYTHONPATH="/app"

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git openssh-client libpq-dev build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir -p /root/.ssh \
 && chmod 700 /root/.ssh \
 && ssh-keyscan github.com >> /root/.ssh/known_hosts

COPY pyproject.toml uv.lock ./

RUN --mount=type=ssh \
    uv sync -v --frozen --no-install-project


RUN --mount=type=ssh \
    uv sync --frozen

CMD ["sh", "-c", "uvicorn ${APP_MODULE} --host ${APP_HOST} --port ${APP_PORT} --app-dir /app/flux_backend --reload"]
