#!/bin/bash
# Runs once when the postgres container initializes an empty data directory.
# Enables pgvector on the main app database, creates a second database for
# OpenFGA's own datastore (same instance, to keep local dev to one
# container), and creates a least-privilege "aperture_app" role.
#
# aperture_app is distinct from the owner role (POSTGRES_USER) on purpose:
# table owners bypass GRANT/REVOKE checks in Postgres, so the running
# application must connect as a non-owner role for the audit_log
# append-only restriction (added in the first Alembic migration) to mean
# anything.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE ROLE aperture_app LOGIN PASSWORD 'aperture_app';
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO aperture_app;
    -- LlamaIndex's PGVectorStore manages its own chunk/vector table (create,
    -- index, drop) entirely on its own, unlike tenants/documents/audit_log
    -- which Alembic owns and aperture_app only has DML grants on. CREATE on
    -- the schema is scoped to new objects, it does not grant any privilege
    -- on tables Alembic already owns.
    GRANT CREATE ON SCHEMA public TO aperture_app;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
    CREATE DATABASE openfga;
    GRANT ALL PRIVILEGES ON DATABASE openfga TO "$POSTGRES_USER";
EOSQL
