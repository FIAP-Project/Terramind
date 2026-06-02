# Terramind — Makefile (macOS / Linux)
# Para Windows, use: .\tasks.ps1 <comando>  ou  python scripts/tasks.py <comando>

.PHONY: help sync up down restart logs ps test fmt lint certs clean

help:
	@echo "Terramind — comandos disponíveis:"
	@echo "  make sync     — uv sync (instalar workspace)"
	@echo "  make up       — docker compose up --build -d"
	@echo "  make down     — docker compose down"
	@echo "  make restart  — restart all containers"
	@echo "  make logs     — tail logs"
	@echo "  make ps       — listar containers"
	@echo "  make test     — uv run pytest"
	@echo "  make fmt      — ruff format"
	@echo "  make lint     — ruff check"
	@echo "  make certs    — gerar certificados TLS de dev (requer mkcert)"
	@echo "  make clean    — remover containers, volumes, caches"

sync:
	uv sync

up:
	docker compose up --build -d
	@echo ""
	@echo "Aguarde alguns segundos e acesse:"
	@echo "  Swagger auth:   https://localhost:8443/auth/docs"
	@echo "  Swagger farm:   https://localhost:8443/farm/docs"
	@echo "  Swagger sensor: https://localhost:8443/sensor/docs"
	@echo "  Swagger alert:  https://localhost:8443/alert/docs"

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

test:
	uv run pytest -q

fmt:
	uv run ruff format .

lint:
	uv run ruff check .

certs:
	@echo "Gerando certificados TLS de dev em infra/nginx/certs/ ..."
	@mkdir -p infra/nginx/certs
	@if command -v mkcert >/dev/null 2>&1; then \
		cd infra/nginx/certs && mkcert -install && mkcert localhost 127.0.0.1 ::1; \
		mv infra/nginx/certs/localhost+2.pem infra/nginx/certs/cert.pem 2>/dev/null || true; \
		mv infra/nginx/certs/localhost+2-key.pem infra/nginx/certs/key.pem 2>/dev/null || true; \
	else \
		echo "mkcert não encontrado. Gerando self-signed via openssl..."; \
		openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
			-keyout infra/nginx/certs/key.pem \
			-out infra/nginx/certs/cert.pem \
			-subj "/CN=localhost" \
			-addext "subjectAltName=DNS:localhost,IP:127.0.0.1"; \
	fi
	@echo "Certificados gerados em infra/nginx/certs/"

clean:
	docker compose down -v
	rm -rf .pytest_cache .ruff_cache **/__pycache__ **/*.egg-info
