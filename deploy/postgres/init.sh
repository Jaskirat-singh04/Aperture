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
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
    CREATE DATABASE openfga;
    GRANT ALL PRIVILEGES ON DATABASE openfga TO "$POSTGRES_USER";
EOSQL
