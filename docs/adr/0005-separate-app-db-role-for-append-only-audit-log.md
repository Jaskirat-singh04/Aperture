# 0005: Separate Database Role For The Running App, Not Just A Grant

## Status

Accepted.

## Context

Hard requirement 6 is that every query writes an append-only audit record. "Append-only"
needs to be enforced by Postgres, not just by application code discipline. The obvious
first approach, `REVOKE UPDATE, DELETE ON audit_log FROM <role>`, only works if the
running application connects as a role that is not the table owner. Postgres table
owners bypass all GRANT/REVOKE checks, a REVOKE against the owner role is silently
meaningless.

## Decision

Use two distinct Postgres roles:

- `aperture` (the Alembic/migration owner role, creates and owns the tables).
- `aperture_app` (a least-privilege role the running application connects as, created in
  `deploy/postgres/init.sh`).

The first Alembic migration grants `aperture_app` `SELECT, INSERT, UPDATE, DELETE` on
`tenants` and `documents`, but only `SELECT, INSERT` on `audit_log`, with an explicit
`REVOKE UPDATE, DELETE` for clarity. `DatabaseSettings` in `aperture.config` exposes both
as separate connection URLs (`sqlalchemy_url` for migrations, `app_sqlalchemy_url` for
the running app), see `aperture.db`.

## Consequences

Two roles and two connection strings to keep straight instead of one, a small amount of
extra configuration. The alternative (one role for everything) would make the
append-only guarantee cosmetic, enforced by nothing, which defeats the point of a
hard requirement meant to resist tampering.
