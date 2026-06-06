# Perguntas Discursivas

> Respostas às três perguntas obrigatórias do PDF `GS_Global_Solution_3ESPY_2026.pdf`.

---

## 1. Quais seriam os principais desafios caso o sistema precisasse atender milhares de usuários simultaneamente?

**Gargalos esperados, do mais provável ao menos provável:**

### Banco de dados (PostgreSQL)
O Postgres aceita ~100 conexões por padrão, e cada serviço já consome até 30
(pool_size 10 + overflow 20). Com mil usuários ativos, somamos facilmente
4 × 30 = 120 conexões só dos serviços. **Soluções:**
- Introduzir **PgBouncer** em modo transaction pooling, reduzindo o footprint
  por conexão a milissegundos;
- **Read replicas** para queries de listagem (`GET /alert/alerts`, séries
  temporais de readings);
- **Particionamento** da tabela `satellite.readings` por mês — a tabela cresce
  ~1 linha por minuto por satellite (~525k/ano por satellite), insustentável para
  queries com `ORDER BY captured_at DESC` sem partição.

### Ingestão de leituras (satellite-service)
Com 10.000 satélites enviando uma leitura por minuto = ~166 req/s — viável,
mas tendo picos de 10× durante ressincronização (satellite que ficou offline
e despeja buffer). **Soluções:**
- **Horizontal scaling** do satellite-service (FastAPI é stateless, basta
  aumentar `replicas` no compose ou no k8s);
- Trocar `POST /readings` síncrono por **ingestão via fila** (satélite publica
  direto no RabbitMQ, satellite-service consome em batch e persiste com
  `COPY` em vez de INSERT individual).

### Barramento de eventos (RabbitMQ)
Topic exchange aguenta dezenas de milhares de msgs/s, mas a queue
`alert-service.readings` é única → consumer único = bottleneck. **Soluções:**
- **Múltiplos consumers** em paralelo (FastAPI lifespan permite N workers);
- **Sharding por country/region** com routing keys diferentes;
- Migrar para **Kafka** se precisar de retenção longa e replay de eventos.

### Autenticação (auth-service)
`/auth/login` envolve bcrypt 12 rounds — ~250ms por verificação. Brute force
de 1k req/s pode CPU-bound a instância. **Soluções:**
- Rate limit já implementado (5 req/min no Nginx) protege contra ataque;
- Para carga legítima, **horizontal scaling** + cache Redis para tokens
  revogados (em vez de query no banco a cada validação).

### JWT e revogação
Hoje cada refresh consulta `auth.refresh_tokens` no Postgres. Em escala,
**cache distribuído** (Redis) de JTIs revogados elimina a query e permite
revogação em tempo real.

### Observabilidade
Logs estruturados são bons, mas sem agregação ficam inúteis em escala.
**Soluções:** ELK/Loki para logs, Prometheus para métricas e Jaeger para
traces distribuídos (o `request_id` já está propagado, falta o tracing).

---

## 2. Quais pontos da arquitetura poderiam ser melhorados futuramente?

Em ordem de prioridade:

### 1. Rate limiting por usuário (não só por IP)
Hoje o limit do Nginx é por IP — um único usuário malicioso atrás de NAT
afeta usuários legítimos no mesmo IP. **Melhoria**: SlowAPI com chave
derivada do JWT (`sub` claim), backend Redis para distribuição entre
réplicas.

### 2. MFA para roles privilegiados
`agronomist` e `admin` deveriam ter TOTP obrigatório. A estrutura do JWT
já suporta um claim `mfa_verified` — falta implementar `pyotp` e fluxo
de enrollment.

### 3. Vault para segredos
`.env` é vulnerável a leak no Git e não suporta rotação automática.
Migrar para HashiCorp Vault, AWS Secrets Manager ou Azure Key Vault
permite rotação programada e auditoria de acesso a segredos.

### 4. Particionamento e retenção de leituras
A tabela `satellite.readings` cresce indefinidamente. Soluções:
- **Particionamento por mês** (PG 16 suporta DECLARATIVE PARTITION);
- **Política de retenção**: manter últimos 90 dias quentes, mover o
  restante para data lake (S3 + Parquet);
- **Agregações materializadas** (médias diárias/semanais) para queries
  de longo prazo.

### 5. Regras de alerta dinâmicas
Hoje o `RuleEngine` tem regras hardcoded com thresholds de fallback.
**Melhoria**: armazenar regras em tabela `alert.rules` editável via
endpoint admin, com expressões compiladas (ex.: `simpleeval` ou DSL própria).
Permite ao agronomista ajustar limites por cultura sem deploy.

### 6. Observabilidade nativa
Adicionar OpenTelemetry SDK em `terramind-shared` — todas as requests e
eventos emitiriam traces correlacionados pelo `request_id`. Exportar para
Tempo/Jaeger.

### 7. Idempotência na ingestão
`POST /readings` deveria aceitar um `Idempotency-Key` header. Hoje, se
um satellite retransmitir a mesma leitura por falha de rede, criamos duplicata.

### 8. Backups e DR
Em produção: snapshots automáticos do volume Postgres (3× ao dia, retenção
30 dias), test de restore mensal, runbook de DR documentado.

### 9. CI/CD
Falta GitHub Actions: lint, testes, build de imagem Docker, security scan
(Trivy), deploy automatizado.

### 10. Testes de carga
k6 ou Locust para validar a capacidade real antes de cada release. Hoje
temos apenas pytest funcional.

---

## 3. Como o sistema poderia evoluir para uma arquitetura distribuída?

O Terramind já está parcialmente distribuído (4 serviços + barramento), mas
ainda compartilha um único Postgres e roda em um único host Docker.
Evolução em camadas:

### Camada 1 — Múltiplos hosts (Kubernetes)
Os 4 serviços já são stateless e containerizados. Migração para k8s exige:
- Helm charts por serviço (parametrizando `replicas`, `resources`);
- **HorizontalPodAutoscaler** baseado em CPU/req-rate;
- **Ingress controller** substituindo o Nginx atual (ou Istio gateway);
- **External-secrets** apontando para Vault;
- StatefulSets para Postgres/RabbitMQ ou (melhor) operadores gerenciados
  (RDS, Amazon MQ, CNPG).

### Camada 2 — Banco distribuído
O banco único é o ponto de não-escalabilidade horizontal. Caminhos:

- **Vertical**: começar com Postgres maior (mais CPU/RAM) + read replicas;
- **Sharding por tenant** (produtor): cada shard contém todas as fazendas
  de um conjunto de produtores. `farm_id` carrega prefixo de shard;
- **CockroachDB / YugabyteDB** quando o sharding manual ficar caro;
- **TimescaleDB** especificamente para `satellite.readings` — otimizado para
  séries temporais, suporta compressão e particionamento automático.

### Camada 3 — Mensageria escalável
RabbitMQ funciona bem até dezenas de milhares de msgs/s. Acima disso:

- **Apache Kafka** com partitioning por `plot_id` permite paralelizar
  consumers sem perder ordem por talhão;
- **Schema Registry** (Avro/Protobuf) substitui Pydantic em runtime para
  validação cross-service.

### Camada 4 — CQRS e read models por região
Separar comandos (writes) dos queries (reads):
- Writes vão para o serviço/região onde o usuário está;
- Reads consultam **read models materializados** localmente em cada
  região via consumer Kafka;
- Latência cai para usuários distantes; throughput de leitura escala
  independentemente.

### Camada 5 — Service mesh
Com 4+ serviços em produção, **Istio** ou **Linkerd** adicionam:
- mTLS automático entre serviços (substitui parcialmente o HMAC dos eventos);
- Circuit breakers (alert-service não derruba satellite-service se travar);
- Retries com backoff;
- Traces distribuídos automaticamente;
- Canary deploys.

### Camada 6 — Edge / Multi-region
Para produtores no Norte e no Sul do Brasil:
- **CDN** (CloudFront/Cloudflare) na borda para assets e cache de respostas
  públicas (catálogo de Crops);
- **Multi-region deployment** com cluster por região, replicação assíncrona
  do banco mestre;
- **Geo-routing** no DNS (Route 53 latency-based) para roteamento à região
  mais próxima.

### Camada 7 — Edge processing nos satélites
Em vez de cada leitura virar um POST HTTP, satélites publicariam via **MQTT**
para um broker regional (HiveMQ, EMQX). Um adapter MQTT→HTTP/Kafka faria a
ponte. Vantagem: protocolo desenhado para IoT (QoS, offline buffering, baixo
consumo de bateria).

### Resumo

A arquitetura atual já é o **passo 1** dessa jornada — microsserviços
stateless, mensageria assíncrona, banco com schemas isolados. Cada um dos
demais passos (k8s, sharding, Kafka, CQRS, mesh, multi-region, MQTT) é uma
evolução incremental que mantém o contrato HTTP/JSON dos clientes inalterado.
