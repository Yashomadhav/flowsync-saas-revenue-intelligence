-- =============================================================================
-- Migration 001: Create Schemas, Extensions, and Roles
-- FlowSync Revenue Intelligence — Medallion Architecture
-- =============================================================================
-- Idempotent: safe to run multiple times.
-- Run order: 001 → 002 → 003 → 004 → 005
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ---------------------------------------------------------------------------
-- Schemas (Medallion layers)
-- ---------------------------------------------------------------------------

-- Bronze: raw ingested data (text columns, append-only)
CREATE SCHEMA IF NOT EXISTS raw;
COMMENT ON SCHEMA raw IS 'Bronze layer: raw ingested data from CSV/API sources. Text columns only, append-only.';

-- Silver: cleaned and typed staging data
CREATE SCHEMA IF NOT EXISTS staging;
COMMENT ON SCHEMA staging IS 'Silver layer: cleaned, typed, and validated staging data. One row per entity.';

-- Gold: aggregated analytics marts
CREATE SCHEMA IF NOT EXISTS marts;
COMMENT ON SCHEMA marts IS 'Gold layer: aggregated analytics-ready fact tables and data marts.';

-- ---------------------------------------------------------------------------
-- Application role (least-privilege for the API)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'flowsync_app') THEN
        CREATE ROLE flowsync_app WITH LOGIN PASSWORD 'flowsync_app_secret';
    END IF;
END
$$;

-- Grant schema usage
GRANT USAGE ON SCHEMA raw TO flowsync_app;
GRANT USAGE ON SCHEMA staging TO flowsync_app;
GRANT USAGE ON SCHEMA marts TO flowsync_app;

-- Grant table-level permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO flowsync_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA staging TO flowsync_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA marts TO flowsync_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO flowsync_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO flowsync_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marts TO flowsync_app;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA raw
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO flowsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO flowsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO flowsync_app;

-- ---------------------------------------------------------------------------
-- Read-only analytics role (for BI tools, Metabase, etc.)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'flowsync_readonly') THEN
        CREATE ROLE flowsync_readonly WITH LOGIN PASSWORD 'flowsync_readonly_secret';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA staging TO flowsync_readonly;
GRANT USAGE ON SCHEMA marts TO flowsync_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA staging TO flowsync_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO flowsync_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA staging
    GRANT SELECT ON TABLES TO flowsync_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts
    GRANT SELECT ON TABLES TO flowsync_readonly;

-- ---------------------------------------------------------------------------
-- dbt role (needs DDL rights for model materialization)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'flowsync_dbt') THEN
        CREATE ROLE flowsync_dbt WITH LOGIN PASSWORD 'flowsync_dbt_secret';
    END IF;
END
$$;

GRANT ALL PRIVILEGES ON SCHEMA raw TO flowsync_dbt;
GRANT ALL PRIVILEGES ON SCHEMA staging TO flowsync_dbt;
GRANT ALL PRIVILEGES ON SCHEMA marts TO flowsync_dbt;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO flowsync_dbt;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO flowsync_dbt;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA marts TO flowsync_dbt;

-- ---------------------------------------------------------------------------
-- Search path configuration
-- ---------------------------------------------------------------------------
ALTER DATABASE flowsync_bi SET search_path TO marts, staging, raw, public;

-- ---------------------------------------------------------------------------
-- Audit log table (public schema, shared)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.audit_log (
    id          BIGSERIAL PRIMARY KEY,
    event_time  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    schema_name TEXT,
    table_name  TEXT,
    operation   TEXT,
    row_count   INTEGER,
    duration_ms NUMERIC(10, 2),
    run_by      TEXT DEFAULT CURRENT_USER,
    notes       TEXT
);

COMMENT ON TABLE public.audit_log IS 'Tracks ETL runs, dbt executions, and data load events.';

-- ---------------------------------------------------------------------------
-- Migration tracking table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    version     TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT
);

INSERT INTO public.schema_migrations (version, description)
VALUES ('001', 'Create schemas, extensions, and roles')
ON CONFLICT (version) DO NOTHING;
