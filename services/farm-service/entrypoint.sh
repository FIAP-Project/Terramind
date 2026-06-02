#!/usr/bin/env sh
set -e

echo "[farm-service] running migrations..."
alembic upgrade head || echo "[farm-service] WARNING: migrations failed, continuing"

echo "[farm-service] starting uvicorn..."
exec uvicorn farm_service.main:app \
    --host 0.0.0.0 \
    --port 8002 \
    --proxy-headers \
    --forwarded-allow-ips="*"
