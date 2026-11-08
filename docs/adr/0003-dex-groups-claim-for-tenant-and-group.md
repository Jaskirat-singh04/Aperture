# 0003: Dex Groups Claim Carries Tenant And Group, With A Prefix Convention

## Status

Accepted.

## Context

Dex's static password connector issues ID tokens with a `groups` claim (a flat list of
strings), there is no separate, native "tenant" claim. Aperture needs both tenant_id and
group membership per user to resolve OpenFGA tuples.

Writing a custom Dex connector would carry a custom claim shape, but that is a
meaningfully larger piece of custom code (a Go plugin) for a problem that a naming
convention solves just as well for a local development identity provider.

## Decision

Encode both in the existing `groups` claim with a prefix convention (see
`deploy/dex/config.yaml`):

- Exactly one `tenant:<tenant_id>` entry per user.
- Zero or more `group:<name>` entries, tenant-scoped by convention, not by the string
  itself. `aperture.auth.oidc` parses this and
  `CurrentUser.openfga_group_ids()` combines tenant_id and group name into the OpenFGA
  group object id (for example `acme-finance`).

## Consequences

This is a local-development convention tied to how Dex is configured here, a real
identity provider used in a later environment would need its own mapping from whatever
claims it issues to tenant_id and group names, but would not need to change the
OpenFGA model or the rest of the auth code, only `aperture.auth.oidc`'s claim parsing.
