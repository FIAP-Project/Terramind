# Capítulo de Cybersecurity — Terramind

> Desafio de Cybersecurity — Global Solution 2026/1
> Atende aos 10 pontos solicitados no PDF `3ES-Cybersecurity-GS2026-1.pdf`.

## Sumário

1. [Análise de Riscos e Ameaças (Threat Modeling) — 2 pts](#1-análise-de-riscos-e-ameaças-threat-modeling--2-pts)
2. [Arquitetura de Segurança (Controles) — 3 pts](#2-arquitetura-de-segurança-controles--3-pts)
3. [Governança e Compliance — 2 pts](#3-governança-e-compliance--2-pts)
4. [Plano de Resiliência e Continuidade — 3 pts](#4-plano-de-resiliência-e-continuidade--3-pts)

---

## 1. Análise de Riscos e Ameaças (Threat Modeling) — 2 pts

### 1.1 Identificação de Ativos (1 pt)

| Ativo | Tipo | Criticidade | Notas |
|---|---|---|---|
| Banco PostgreSQL (schemas `auth`, `farm`, `satellite`, `alert`) | Dado | **Crítica** | Contém: emails, hashes de senha, coordenadas GPS de propriedades, histórico de leituras. |
| Tokens JWT (access + refresh) | Credencial | **Crítica** | Acesso direto aos endpoints autenticados. |
| Segredo `JWT_SECRET` | Segredo | **Crítica** | Comprometimento → forjar JWT arbitrário. |
| Segredo `EVENT_SIGNING_SECRET` | Segredo | Alta | Comprometimento → forjar eventos no RabbitMQ. |
| Credenciais Postgres / RabbitMQ | Segredo | Alta | Comprometimento → acesso direto a banco e fila. |
| Stream de eventos no RabbitMQ | Dado | Alta | Telemetria em trânsito; assinada com HMAC. |
| Endpoint público `/auth/login` e `/auth/register` | Superfície | Alta | Alvo de força bruta e enumeração. |
| Endpoint `/satellite/satellites/{id}/readings` | Superfície | Alta | Alvo de injeção de leituras falsas. |
| satélites IoT físicos (futuro) | Dispositivo | Média | Hoje simulados; em produção precisam de mTLS ou API Key dedicada. |
| Logs aplicacionais com `request_id` | Dado de auditoria | Média | Fonte de detecção de incidentes. |
| Certificados TLS | Segredo | Alta | Em produção, rotacionados via ACME. |

### 1.2 Modelo de Ameaças (1 pt)

Modelo **STRIDE** aplicado à solução. Listamos quatro vetores de ataque
plausíveis (o PDF exige no mínimo três):

#### Ameaça 1 — Spoofing: Falsificação de leituras de satélites

- **Cenário**: atacante descobre `serial_number` de um satellite e envia leituras
  forjadas via `POST /satellite/satellites/{id}/readings`.
- **Impacto**: alertas falsos confundem o produtor, suprimem alertas reais ou
  travam ações operacionais.
- **Mitigações implementadas**:
  - Endpoint exige `Authorization: Bearer <access_token>` válido;
  - Em produção: API Key dedicada por satellite + assinatura HMAC do payload;
  - Rate limit no Nginx (30 req/s global) impede flooding.

#### Ameaça 2 — Tampering: Adulteração de eventos no barramento

- **Cenário**: invasor com acesso à rede interna (lateral movement) publica
  eventos `satellite.reading.recorded` ou `alert.resolved` forjados no RabbitMQ.
- **Impacto**: alertas spam ou alertas reais marcados como resolvidos
  silenciosamente.
- **Mitigações implementadas**:
  - Toda mensagem leva header `x-signature` com HMAC-SHA256 sobre o body;
  - Consumers (alert-service) validam a assinatura antes de processar
    (`terramind_shared.events.signing.verify_signature`);
  - Mensagens sem assinatura ou com assinatura inválida são descartadas
    com log de alerta.

#### Ameaça 3 — Denial of Service: Flood na ingestão ou no login

- **Cenário**: bot envia milhares de POSTs em `/satellite/.../readings` ou
  tentativas de senha em `/auth/login` para esgotar conexões do banco ou
  travar o autenticador.
- **Impacto**: indisponibilidade da plataforma; perda de leituras legítimas.
- **Mitigações implementadas**:
  - Rate limit em duas camadas: Nginx (5 req/min em `/auth/login`, 30 req/s
    global) e SlowAPI por endpoint (roadmap);
  - Connection pool do SQLAlchemy limitado (`pool_size=10, max_overflow=20`)
    — falha rápido em vez de derrubar o Postgres;
  - `client_max_body_size 1m` no Nginx bloqueia payload bombing;
  - Healthchecks reiniciam containers travados automaticamente.

#### Ameaça 4 — Information Disclosure: Vazamento de coordenadas GPS

- **Cenário**: bug em controller ou error handler expõe lat/lng de fazendas
  no body de erro ou em log público.
- **Impacto**: privacidade do produtor; risco físico (furto, sabotagem).
- **Mitigações implementadas**:
  - Handler global de erro nunca inclui stack trace ou conteúdo do request
    nas respostas (`packages/shared/.../middleware/error_handler.py`);
  - Logs são estruturados (`structlog`) e ficam server-side, correlacionáveis
    apenas via `request_id`;
  - RBAC: usuários `producer` só veem suas próprias fazendas (verificado em
    `FarmService.get_owned`).

---

## 2. Arquitetura de Segurança (Controles) — 3 pts

### 2.1 Controles de Acesso (1 pt)

- **Autenticação JWT HS256** com TTL curto: `access_token` = 15 min,
  `refresh_token` = 7 dias.
- **Refresh rotation com rastreamento**: cada refresh tem um JTI persistido
  em `auth.refresh_tokens`. Ao consumir, o JTI é marcado como `revoked=true`
  e um novo par é emitido — refresh reutilizado falha com 401.
- **RBAC hierárquico**: enum `Role` com três níveis
  (`PRODUCER < AGRONOMIST < ADMIN`). Endpoints sensíveis usam
  `Depends(require_role(Role.ADMIN))` (ex.: criar/editar `Crop` no catálogo)
  ou `Role.AGRONOMIST` (ex.: resolver alerta).
- **Princípio do menor privilégio**: usuários só veem dados de suas próprias
  fazendas, verificado no service layer (não confiamos no client).
- **MFA (roadmap)**: TOTP via `pyotp` para `admin` e `agronomist` —
  estrutura do JWT já suporta claim adicional sem migração.
- **Política de senhas forte**: 12–128 chars com upper + lower + digit +
  símbolo, validada por regex no DTO `RegisterRequest`.

### 2.2 Proteção de Dados (1 pt)

**Em trânsito:**
- Nginx termina TLS 1.2+ no `8443` com HSTS (`max-age=31536000`);
- Cipher suite restrita a `HIGH:!aNULL:!MD5`;
- Redirect 301 automático de `8080` (HTTP) para HTTPS.

**Em repouso:**
- Senhas: SHA256 pre-hash (resolve limite de 72 bytes do bcrypt) + bcrypt
  12 rounds via `passlib`;
- Segredos lidos exclusivamente do `.env` (nunca hardcoded);
- Em produção: ativar PG TDE (Transparent Data Encryption) ou criptografia
  no volume EBS/Persistent Disk;
- Backups do volume `pgdata` (Docker volume) replicados para storage
  separado (recomendação documentada).

**Minimização e anonimização:**
- Não coletamos CPF, telefone ou nome completo obrigatório;
- Endpoint `DELETE /auth/me` apaga completamente o usuário (cascade nos
  refresh_tokens) atendendo ao direito de exclusão da LGPD;
- Roadmap: endpoint de export agregado (médias mensais) sem identificadores
  diretos para fins de pesquisa/governo.

### 2.3 Segurança da Infraestrutura (1 pt)

- **Security headers** no Nginx em todas as respostas:
  - `Strict-Transport-Security`,
  - `X-Content-Type-Options: nosniff`,
  - `X-Frame-Options: DENY`,
  - `Referrer-Policy: no-referrer`,
  - `Permissions-Policy` restrita,
  - `Content-Security-Policy` com `default-src 'self'`;
- Os mesmos headers são aplicados também no `SecurityHeadersMiddleware` de
  cada serviço, como defesa em profundidade caso o gateway seja bypassado;
- **Network isolation**: os 4 serviços de aplicação (`auth`, `farm`, `satellite`,
  `alert`) **não publicam portas** ao host — usam apenas `expose:` para a rede
  interna `terramind-net` e só são alcançáveis via Nginx (porta 8443/8080).
  Postgres, RabbitMQ e Redis publicam portas apenas em `127.0.0.1` (loopback),
  o que permite acesso de ferramentas de dev locais (psql, RabbitMQ UI) sem
  expor à LAN. Em produção, mesmo o bind em `127.0.0.1` deve ser removido;
- **Zero Trust interno**: HMAC-SHA256 obrigatório em todo evento RabbitMQ —
  não confiamos no barramento mesmo sendo interno;
- **Logs estruturados** (`structlog`) com `request_id` propagado de
  ponta a ponta para investigação forense;
- **Healthchecks** em todos os containers — Compose reinicia o que falha;
- **Imagens base mínimas** (Alpine onde possível) para reduzir superfície
  de ataque;
- **Roadmap**: introduzir Vault / AWS Secrets Manager no lugar do `.env`;
  WAF (ModSecurity) no Nginx; SIEM (ELK) para correlação de eventos.

---

## 3. Governança e Compliance — 2 pts

### 3.1 Alinhamento ISO 27001 (1 pt)

Mapeamento dos controles aplicados aos domínios da ISO 27001:2022:

| Domínio | Como o Terramind atende |
|---|---|
| A.5 — Políticas de SI | Documento de cybersecurity (este arquivo); política de senhas codificada em validador Pydantic. |
| A.6 — Organização da SI | RBAC com três papéis claros; cada serviço com escopo de responsabilidade único. |
| A.8 — Gestão de ativos | Inventário documentado na seção 1.1; `request_id` para rastreabilidade. |
| A.9 — Controle de acesso | JWT + refresh rotation; RBAC hierárquico; revogação por JTI; LGPD delete. |
| A.10 — Criptografia | TLS 1.2+ em trânsito; bcrypt para senhas; HMAC para eventos; segredos via `.env`. |
| A.12 — Operações | Healthchecks; logs estruturados; backups (volume Postgres). |
| A.13 — Comunicações | Network isolation; gateway único; security headers em todas as respostas. |
| A.14 — Aquisição e desenvolvimento | Validação de entrada (Pydantic); migrações versionadas (Alembic); CI com ruff + pytest. |
| A.16 — Gestão de incidentes | Plano detalhado na seção 4. |
| A.17 — Continuidade | Docker Compose declarativo permite redeployar rapidamente; backup do volume Postgres. |
| A.18 — Conformidade | LGPD coberto na seção 3.2. |

**Gestão de Riscos:** o ciclo PDCA é representado pelo plano de threat
modeling (seção 1), pelos controles (seção 2), pela documentação de
incidentes (seção 4) e pela revisão periódica (planejada bimestral).

### 3.2 Privacidade — LGPD (1 pt)

| Princípio LGPD (art. 6º) | Aplicação no Terramind |
|---|---|
| Finalidade | Coletamos email + dados de propriedade exclusivamente para autenticar e monitorar a produção. Sem uso secundário. |
| Adequação | Os dados pessoais coletados (email, lat/lng da fazenda) são compatíveis com a finalidade declarada. |
| Necessidade | Não coletamos CPF, telefone, RG ou outros dados sensíveis. |
| Livre acesso | `GET /auth/me` retorna todos os dados do titular a qualquer momento. |
| Qualidade dos dados | Validação Pydantic garante formatos corretos; `updated_at` rastreia última alteração. |
| Transparência | Documentação pública (este arquivo + README). |
| Segurança | Todos os controles da seção 2. |
| Prevenção | Threat modeling (seção 1) + plano de IR (seção 4). |
| Não discriminação | Nenhum processamento automatizado para perfilamento. |
| Responsabilização | Logs estruturados auditáveis por `request_id`. |

**Bases legais aplicadas:**
- **Consentimento (art. 7º, I)** para criação da conta (email e dados de
  propriedade) — implícito no fluxo de `register`;
- **Execução de contrato (art. 7º, V)** para processar leituras e gerar alertas;
- **Legítimo interesse (art. 7º, IX)** para logs de auditoria e detecção de
  fraude — limitado e documentado.

**Direitos do titular implementados:**
- **Acesso** (art. 18, II): `GET /auth/me`;
- **Correção** (art. 18, III): em roadmap (`PUT /auth/me`);
- **Anonimização/Eliminação** (art. 18, VI): `DELETE /auth/me` apaga
  completamente o usuário e seus refresh tokens (cascade FK);
- **Portabilidade** (art. 18, V): roadmap — export JSON de todas as
  fazendas/plots/leituras do usuário.

**Notificação de incidente (art. 48):** plano detalhado na seção 4.5 — janela
máxima de 72h para comunicação à ANPD e aos titulares afetados.

---

## 4. Plano de Resiliência e Continuidade — 3 pts

Plano de Resposta a Incidentes (IR) baseado no framework NIST 800-61
(Preparação → Detecção → Contenção → Erradicação → Recuperação → Lições).

### 4.1 Preparação (T-∞)

- Documentação de threat model (seção 1) revisada bimestralmente;
- Backups do volume `pgdata` para storage externo (recomendação para produção);
- Runbook documentado (este capítulo);
- Lista de contatos de responsáveis técnicos e jurídicos (DPO) mantida atualizada.

### 4.2 Detecção (T+0)

Fontes de telemetria que disparam o início do plano:

- **Aplicacional**: pico de eventos `auth.failed` no log do auth-service;
- **Gateway**: pico de `429 Too Many Requests` no Nginx;
- **Barramento**: warning de "dropping unsigned/invalid event" no alert-service;
- **Banco**: queries lentas ou crescimento anômalo em `auth.refresh_tokens`;
- **Manual**: relato de produtor sobre acesso indevido ou alerta falso.

Todos os logs estruturados carregam `request_id`, permitindo reconstruir
a sequência de chamadas pelas quatro APIs.

### 4.3 Contenção (T+15 min)

Ação imediata para parar o sangramento, sem ainda investigar causa raiz:

```sql
-- 1. Revogar TODOS os refresh tokens (força re-login)
UPDATE auth.refresh_tokens SET revoked = true;
```

```bash
# 2. Bloquear IPs suspeitos no Nginx (adicionar `deny <ip>;` ao server block)
# 3. Rotacionar JWT_SECRET no .env (invalida access tokens imediatamente)
# 4. Restart auth-service para carregar novo secret
docker compose restart auth-service
```

```sql
-- 5. Se vetor for leitura forjada: pausar ingestão temporariamente
-- (alternativa: mudar status do satellite para "maintenance")
UPDATE satellite.satellites SET status = 'maintenance' WHERE id IN (...);
```

### 4.4 Erradicação (T+1 h)

Identificação e remoção da causa raiz:

1. **Análise forense**: filtrar logs pelo `request_id` ou pelo IP envolvido
   no incidente;
2. **Identificação do vetor**: foi credencial roubada? bug em validação?
   evento HMAC forjado? exposição de segredo no Git history?
3. **Patch**: aplicar fix no código (PR + revisão obrigatória);
4. **Rotação completa de segredos**:
   - `JWT_SECRET`, `EVENT_SIGNING_SECRET`,
   - Senha do Postgres, RabbitMQ, Redis,
   - Certificados TLS (`make certs` novamente em produção via ACME);
5. **Auditoria de dados**: rodar query para detectar leituras suspeitas
   (ex.: valores fora de envelope físico) e marcá-las;
6. **Atualizar threat model** com o novo vetor identificado.

### 4.5 Recuperação (T+24 h)

Restauração do serviço a estado limpo:

1. **Restore de backup** se houver indício de corrupção do banco;
2. **Validação de integridade**:
   - Conferir contagem de leituras esperada vs presente;
   - Verificar que assinaturas HMAC de eventos arquivados batem;
3. **Re-enable de ingestão**: voltar satélites para `status=active`;
4. **Comunicação aos usuários**:
   - Email/in-app aos produtores afetados (LGPD art. 48 — em até 72h);
   - Notificação à ANPD se houver tratamento de dado pessoal comprometido;
5. **Smoke test end-to-end**: `python scripts/seed.py` + `simulate_readings.py`
   confirma fluxo completo funcionando.

### 4.6 Lições aprendidas (T+72 h)

- **Postmortem documentado**: timeline, impacto, root cause, ações tomadas,
  ações pendentes;
- **Atualizar runbook** com novos passos descobertos;
- **Atualizar testes** automatizados para cobrir o vetor;
- **Revisão de threat model** (seção 1) e priorização de novas mitigações;
- **Treinamento** com a equipe técnica.

### 4.7 Timeline resumida

| Fase | Tempo desde detecção | Ações |
|---|---|---|
| Detecção | T+0 | Alarme dispara via log ou relato. |
| Contenção | T+15 min | Revogar tokens, bloquear IPs, rotacionar JWT_SECRET. |
| Erradicação | T+1 h | Identificar vetor, aplicar patch, rotacionar todos os segredos. |
| Recuperação | T+24 h | Restaurar backup, validar integridade, comunicar usuários. |
| Notificação ANPD | T+72 h (LGPD) | Comunicado oficial à autoridade e titulares se houver dado pessoal afetado. |
| Lições aprendidas | T+72 h em diante | Postmortem, atualização de testes e treinamento. |

---

## Apêndice — Mapeamento dos 10 pontos pedidos no PDF

| Item PDF | Pontos | Local atendido |
|---|---|---|
| Identificação de Ativos | 1 | 1.1 |
| Modelo de Ameaças (≥3 vetores) | 1 | 1.2 (4 vetores: spoofing, tampering, DoS, info disclosure) |
| Controles de Acesso | 1 | 2.1 |
| Proteção de Dados | 1 | 2.2 |
| Segurança da Infraestrutura | 1 | 2.3 |
| ISO 27001 — Gestão de Riscos | 1 | 3.1 |
| Privacidade — LGPD | 1 | 3.2 |
| Plano de Resposta a Incidentes | 3 | Seção 4 (Detecção, Contenção, Erradicação, Recuperação, Lições) |
| **Total** | **10** | ✔ |
