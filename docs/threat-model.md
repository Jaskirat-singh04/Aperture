# Threat Model

An outline of the threats Aperture's design is meant to resist. Each heading below is a
risk category, not yet a full analysis, filled in as the corresponding feature is built.

## Prompt Injection Through Documents

A document's content instructs the model to ignore the user's permissions, leak other
documents, or change its own behavior.

## Permission Drift

A document's access permissions change at the source (Google Drive, file share) but the
OpenFGA tuples describing who can view it fall out of sync, granting stale access.

## Cross-Tenant Leakage

A user in one tenant retrieves or is answered with content that belongs to another
tenant, see `deploy/openfga/model.fga` and
[ADR 0007](adr/0007-structural-tenant-isolation-in-openfga-model.md) for how the
authorization model is meant to prevent this structurally.

## Data Exfiltration Through Citations

An answer's citations reveal the existence, title, or metadata of a document the asking
user is not permitted to read, even if the answer text itself does not quote it.

## Audit Log Tampering

A user, an operator, or a bug modifies or deletes an audit record after the fact, see
[ADR 0005](adr/0005-separate-app-db-role-for-append-only-audit-log.md) for the database
level control meant to prevent this.
