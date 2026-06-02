FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv para gerenciar workspace
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

WORKDIR /app

# Copiar workspace root + shared + service
COPY pyproject.toml /app/pyproject.toml
COPY packages/shared /app/packages/shared
COPY services/auth-service /app/services/auth-service

# Instalar deps do serviço (resolve workspace)
RUN uv sync --package auth-service

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/services/auth-service

COPY services/auth-service/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
