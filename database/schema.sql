-- =============================================================================
-- FlowSync Revenue Intelligence — Master Schema
-- =============================================================================
-- Runs all migrations in order. Safe to re-run (idempotent).
-- Usage:
--   psql $DATABASE_URL -f database/schema.sql
--   docker exec -i flowsync_postgres psql -U flowsync -d flowsync_bi -f /schema.sql
-- =============================================================================

\echo '============================================================'
\echo 'FlowSync Revenue Intelligence — Schema Initialization'
\echo '============================================================'

\echo ''
\echo '[001] Creating schemas and extensions...'
\ir migrations/001_create_schemas.sql

\echo ''
\echo '[002] Creating raw (bronze) tables...'
\ir migrations/002_raw_tables.sql

\echo ''
\echo '[003] Creating staging (silver) tables...'
\ir migrations/003_staging_tables.sql

\echo ''
\echo '[004] Creating marts (gold) tables...'
\ir migrations/004_marts_tables.sql

\echo ''
\echo '[005] Creating views and functions...'
\ir migrations/005_views_and_functions.sql

\echo ''
\echo '============================================================'
\echo 'Schema initialization complete!'
\echo '============================================================'
