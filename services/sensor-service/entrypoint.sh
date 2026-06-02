#!/usr/bin/env sh
set -e

echo "[sensor-service] running migrations..."
alembic upgrade head || echo "[sensor-service] WARNING: migrations failed, continuing"

echo "[sensor-service] starting uvicorn..."
exec uvicorn sensor_service.main:app \
    --host 0.0.0.0 \
    --port 8003 \
    --proxy-headers \
    --forwarded-allow-ips="*"
