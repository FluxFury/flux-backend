# Dockerfile

FROM python:3.12-slim-bullseye

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client  \
    git \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/ 

RUN mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts


RUN --mount=type=ssh \ 
    --mount=type=bind,source=uv.lock,target=uv.lock \ 
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \ 
    uv sync -v --frozen --no-install-project 

COPY . .

COPY ../../pyproject.toml ../../uv.lock ./

RUN --mount=type=ssh \ 
    uv sync --frozen 


CMD ["bash"]
