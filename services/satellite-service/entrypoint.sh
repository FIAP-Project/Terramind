#!/usr/bin/env sh
set -e

echo "[satellite-service] running migrations..."
alembic upgrade head || echo "[satellite-service] WARNING: migrations failed, continuing"

echo "[satellite-service] starting uvicorn..."
exec uvicorn satellite_service.main:app \
    --host 0.0.0.0 \
    --port 8003 \
    --proxy-headers \
    --forwarded-allow-ips="*"
