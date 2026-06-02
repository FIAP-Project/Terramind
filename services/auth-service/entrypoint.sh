#!/usr/bin/env sh
set -e

echo "[auth-service] running migrations..."
alembic upgrade head || echo "[auth-service] WARNING: migrations failed, continuing"

echo "[auth-service] starting uvicorn..."
exec uvicorn auth_service.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --proxy-headers \
    --forwarded-allow-ips="*"
