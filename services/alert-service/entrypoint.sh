#!/usr/bin/env sh
set -e

echo "[alert-service] running migrations..."
alembic upgrade head || echo "[alert-service] WARNING: migrations failed, continuing"

echo "[alert-service] starting uvicorn..."
exec uvicorn alert_service.main:app \
    --host 0.0.0.0 \
    --port 8004 \
    --proxy-headers \
    --forwarded-allow-ips="*"
