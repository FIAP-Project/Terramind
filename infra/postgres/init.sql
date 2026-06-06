-- Inicialização do Postgres do Terramind.
-- Executado uma única vez quando o volume está vazio.

-- Extensões obrigatórias
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Schemas por serviço (as migrations Alembic recriam se necessário,
-- mas garantimos a existência aqui também para evitar race conditions).
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS farm;
CREATE SCHEMA IF NOT EXISTS satellite;
CREATE SCHEMA IF NOT EXISTS alert;
