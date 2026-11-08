# 0006: One Postgres Instance, Two Databases, For App Data And OpenFGA

## Status

Accepted.

## Context

OpenFGA needs its own Postgres-backed datastore (tuples, authorization models). It could
run against a separate Postgres container, or against a second database inside the same
Postgres instance that already holds Aperture's own tables and the pgvector store.

## Decision

One Postgres container (`pgvector/pgvector:pg16`), two databases: `aperture` (app
tables, pgvector) and `openfga` (OpenFGA's own schema). Created by
`deploy/postgres/init.sh` at container init.

This is the simpler option for a local, single-machine development stack, one fewer
container to start, health-check and tear down, with no shared-instance drawback that
matters at this scale (the two databases do not share tables or roles beyond the
instance-level superuser).

## Consequences

A production deployment with different availability, backup or scaling requirements for
OpenFGA's data versus the app's data would likely want to split these back into separate
instances, that is a deployment-time decision (see `deploy/terraform-helm-placeholder/`
for where that configuration would eventually live), not a code change.
