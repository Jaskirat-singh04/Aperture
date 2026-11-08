# 0007: Tenant Isolation Is Structural In The OpenFGA Model, Not Just In The Tuples

## Status

Accepted.

## Context

Hard requirement 2 is that a user in tenant A must never retrieve tenant B's content.
The straightforward way to model this in OpenFGA is to only ever write `viewer` tuples
for users within the correct tenant, and trust that ingestion code never writes a tuple
across tenants. That makes tenant isolation a property of the application code writing
tuples, not of the authorization model itself.

## Decision

`deploy/openfga/model.fga` defines `can_view` as an intersection, not just the viewer
union:

```
define can_view: viewer and member from tenant
```

A user must be a `viewer` (direct or via group) AND a `member` of the tenant the
document belongs to (`tenant from tenant`, OpenFGA's tupleset-to-userset relation). If a
`direct_viewer` or `group_viewer` tuple is ever mistakenly written across tenants, the
tenant membership check still blocks access. Retrieval should call `can_view`, not
`viewer`, for exactly this reason (see `aperture.retrieval.service`).

## Consequences

Every document needs exactly one `tenant` tuple pointing at a `tenant` object, and every
tenant needs `member` tuples for its users, this is a small amount of extra bookkeeping
in `deploy/openfga/seed.py` and future ingestion code. In return, tenant isolation does
not depend on ingestion code always getting tuple writes right, it is checked twice.
