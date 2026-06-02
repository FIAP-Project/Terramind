FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY packages/shared /app/packages/shared
COPY services/sensor-service /app/services/sensor-service

RUN uv sync --package sensor-service

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/services/sensor-service

COPY services/sensor-service/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8003

ENTRYPOINT ["/entrypoint.sh"]
