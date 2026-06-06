# Terramind — Plataforma de Monitoramento Agrícola

> **FIAP — 3ESPY — Global Solution 2026/1 — ODS 9 (Indústria, Inovação e Infraestrutura)**
> Tema: *Sistema de agricultura inteligente — monitoramento de produtividade e redução de perdas*

Backend distribuído em microsserviços para coletar leituras de sensores
agrícolas (umidade do solo, temperatura, pluviometria), analisá-las contra
limites ideais por cultura e gerar alertas quando há risco de perda de
produtividade.


## 👥 Integrantes do Grupo

| Nome completo | RM |
|---|---|
| *Pedro Henrique Martins Alves dos Santos* | *558107* |
| *Felipe Cerboncini Cordeiro* | *554909* |
| *Anthony K. Motobe* | *558488* |
| *Milena Codinhoto da Silva* | *554682* |
| *Evellyn Valencia* | *557929* |

---

---

## Sumário

- [Arquitetura](#arquitetura)
- [Stack técnica](#stack-técnica)
- [Como rodar (macOS / Linux)](#como-rodar-macos--linux)
- [Como rodar (Windows)](#como-rodar-windows)
- [Endpoints e Swagger](#endpoints-e-swagger)
- [Demo end-to-end](#demo-end-to-end)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Segurança](#segurança)
- [Documentação adicional](#documentação-adicional)

---

## Arquitetura

```
                    ┌──────────────────┐
                    │   Nginx (8443)   │  TLS, rate limit, security headers
                    └────────┬─────────┘
            ┌────────────────┼─────────────────┬──────────────┐
            ▼                ▼                 ▼              ▼
       auth-svc         farm-svc          sensor-svc      alert-svc
       (8001)           (8002)            (8003)          (8004)
            │                │                 │              ▲
            └────────────────┴─── PostgreSQL ──┘              │
                                                              │
                       sensor.reading.recorded                │
                  publica ──────────────────▶ RabbitMQ ───────┘
                                                consumer
```

- **auth-service**: registro, login, JWT HS256 (access 15min + refresh 7d), RBAC (producer/agronomist/admin), LGPD delete.
- **farm-service**: CRUD de Farms, Plots (talhões) e catálogo de Crops (culturas).
- **sensor-service**: CRUD de Sensors e ingestão de Readings. Publica `sensor.reading.recorded` no barramento.
- **alert-service**: consome `sensor.reading.recorded`, aplica rule engine, gera Alerts e publica `alert.triggered`.
- **shared package (`terramind-shared`)**: config base, ORM, segurança (JWT, hashing, RBAC), middleware (request_id, security_headers, error_handler) e barramento de eventos com assinatura HMAC.

Diagrama detalhado em [`docs/architecture.md`](docs/architecture.md).

---

## Stack técnica

- **Linguagem**: Python 3.12
- **Framework**: FastAPI + Uvicorn (async)
- **ORM**: SQLAlchemy 2.0 async + asyncpg + Alembic
- **DTOs/Validação**: Pydantic 2 + pydantic-settings
- **Segurança**: python-jose (JWT HS256), passlib[bcrypt] (hashing)
- **Mensageria**: RabbitMQ (aio-pika) com HMAC-SHA256 em todas as mensagens
- **Banco**: PostgreSQL 16 (CITEXT + UUID + pgcrypto) com schemas isolados por serviço
- **Gateway**: Nginx 1.27 com TLS 1.2+, rate limiting e security headers
- **Workspace**: uv (workspace única com `packages/*` e `services/*`)
- **Task runner**: `python scripts/tasks.py` (cross-platform)

---

## Como rodar (macOS / Linux)

### Pré-requisitos
- Docker Desktop 4.x ou Docker Engine + Compose v2
- `mkcert` para gerar TLS de dev: `brew install mkcert`

### Passos

```bash
# 1. Copie o .env de exemplo
cp .env.example .env

# 2. Gere certificados TLS para o gateway local
python scripts/tasks.py certs

# 3. Suba todo o stack
python scripts/tasks.py up

# 4. Em outro terminal, popule dados demo
python scripts/seed.py

# 5. (opcional) simule leituras periódicas
python scripts/simulate_readings.py --interval 3 --cycles 30
```

Acesse os Swaggers:
- https://localhost:8443/auth/docs
- https://localhost:8443/farm/docs
- https://localhost:8443/sensor/docs
- https://localhost:8443/alert/docs

> O certificado é self-signed em dev — aceite o aviso do navegador ou use `mkcert -install` para confiar localmente.

Outros comandos:
```bash
python scripts/tasks.py logs      # logs em tempo real
python scripts/tasks.py ps        # status dos containers
python scripts/tasks.py test      # roda pytest
python scripts/tasks.py fmt       # ruff format
python scripts/tasks.py lint      # ruff check
python scripts/tasks.py down      # derruba o stack
python scripts/tasks.py clean     # remove volumes e caches
```

---

## Como rodar (Windows)

### Pré-requisitos
- **Docker Desktop com WSL2** habilitado ([guia oficial](https://docs.docker.com/desktop/install/windows-install/))
- **Python 3.12+** ([python.org](https://www.python.org/downloads/) — durante a instalação, marque "Add python.exe to PATH")
- **uv** (gerenciador Python): `pip install uv` ou `irm https://astral.sh/uv/install.ps1 | iex`
- **Git for Windows** (já configura line endings corretos via `.gitattributes` do projeto)
- `mkcert` via Winget: `winget install -e --id FiloSottile.mkcert --accept-package-agreements --accept-source-agreements`

### Passos no PowerShell

```powershell
# 1. Configure o .env
Copy-Item .env.example .env

# 2. Gere certificados TLS de dev
python scripts\tasks.py certs

# 3. Suba todo o stack
python scripts\tasks.py up

# 4. Em outro PowerShell, popule dados demo
python scripts\seed.py

# 5. (opcional) simule leituras
python scripts\simulate_readings.py --interval 3 --cycles 30
```

Demais comandos:
```powershell
python scripts\tasks.py logs
python scripts\tasks.py test
python scripts\tasks.py down
python scripts\tasks.py clean
```

### Notas Windows-específicas

- **Line endings**: o arquivo `.gitattributes` força LF nos shell scripts/Dockerfiles que rodam dentro dos containers Linux. Se você ver `bad interpreter: /usr/bin/env\r`, rode `git add --renormalize . && git commit` para normalizar.
- **bcrypt**: usamos `passlib[bcrypt]` (wheel pré-compilado) para evitar a necessidade de Visual C++ Build Tools.
- **Docker Desktop**: precisa estar com WSL2 ativo; abra "Settings → General → Use WSL 2 based engine".
- **Encoding**: o Python deste projeto sempre usa UTF-8 explicitamente nos arquivos de configuração.

---

## Endpoints e Swagger

Cada serviço expõe documentação OpenAPI auto-gerada. Resumo:

| Serviço | Path base | Endpoints principais |
|---|---|---|
| auth   | `/auth/...`   | POST `/register`, POST `/login`, POST `/refresh`, GET `/me`, DELETE `/me` |
| farm   | `/farm/...`   | CRUD `/farms`, CRUD `/plots`, CRUD `/crops` |
| sensor | `/sensor/...` | CRUD `/sensors`, POST/GET `/sensors/{id}/readings` |
| alert  | `/alert/...`  | GET `/alerts`, GET `/alerts/{id}`, PATCH `/alerts/{id}/resolve` |

Todos exigem `Authorization: Bearer <access_token>`, exceto `/auth/register`, `/auth/login` e `/auth/refresh`.

Formato unificado de erro:
```json
{
  "error": {
    "code": 422,
    "message": "validation failed",
    "request_id": "f0e1...",
    "details": [{ "loc": ["body", "email"], "msg": "...", "type": "..." }]
  }
}
```

---

## Demo end-to-end

```bash
# 1. Sobe o stack e popula demo
python scripts/tasks.py up && uv run python scripts/seed.py

# 2. Inicia simulador de leituras (background)
uv run python scripts/simulate_readings.py --interval 2 --cycles 30

# 3. Login para obter token
TOKEN=$(curl -ks -X POST https://localhost:8443/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@gmail.com","password":"Terramind#Admin2026"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 4. Confere alertas gerados pelo alert-service
curl -ks https://localhost:8443/alert/alerts \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Esperado: leituras fora do range geram alertas com `severity` warning/critical
e `rule_id` (ex.: `humidity.below_min`, `temperature.above_max`, `rainfall.flood_risk`).

---

## Estrutura de pastas

```
Terramind/
├── packages/shared/                         # terramind-shared (config, db, security, events, middleware)
├── services/
│   ├── auth-service/    (8001)
│   ├── farm-service/    (8002)
│   ├── sensor-service/  (8003)
│   └── alert-service/   (8004)
├── infra/
│   ├── nginx/           # gateway TLS
│   └── postgres/        # init.sql
├── docs/
│   ├── architecture.md
│   ├── cybersecurity.md
│   ├── discursive_questions.md
│   └── diagrams/
├── scripts/
│   ├── tasks.py         # task runner cross-platform
│   ├── seed.py          # dados demo
│   └── simulate_readings.py
├── docker-compose.yml
└── pyproject.toml       # workspace uv
```

---

## Segurança

Resumo dos controles aplicados (detalhes em [`docs/cybersecurity.md`](docs/cybersecurity.md)):

- TLS 1.2+ no gateway com HSTS + security headers
- JWT HS256 com TTL curto (15 min) + refresh com rotação e revogação por JTI
- Senhas: SHA256 pre-hash + bcrypt 12 rounds
- RBAC hierárquico (`producer < agronomist < admin`)
- Rate limit em dois níveis: Nginx (5 req/min em `/auth/login`, 30 req/s global) e por endpoint
- HMAC-SHA256 em todas as mensagens do RabbitMQ
- Schemas Postgres isolados por serviço
- LGPD: endpoint `DELETE /auth/me` para exclusão completa do usuário (cascade nos tokens)
- Logs estruturados com `request_id` para correlação ponta a ponta
- Respostas de erro sem stack trace ou detalhes internos do ORM

---

## Documentação adicional

- [`docs/architecture.md`](docs/architecture.md) — Documento Arquitetural (entregável #2 do PDF)
- [`docs/cybersecurity.md`](docs/cybersecurity.md) — Capítulo de Cybersecurity (10 pts)
- [`docs/discursive_questions.md`](docs/discursive_questions.md) — Respostas às 3 perguntas obrigatórias
- [`docs/diagrams/architecture.mmd`](docs/diagrams/architecture.mmd) — Diagrama Mermaid editável
