# 0008: Custom Code For The Audit Writer, No Library

## Status

Accepted.

## Context

Hard requirement 6 needs an append-only audit record per query (user, tenant, question,
document IDs used, timestamp). There are generic audit-logging libraries for Python and
SQLAlchemy (for example `sqlalchemy-continuum`, or building on `sqlalchemy` events),
mostly aimed at tracking row-level change history across arbitrary tables.

## Decision

Write `aperture.audit.writer.record_query` by hand: one function, one `INSERT` into the
purpose-built `audit_log` table, no library.

The generic audit-history libraries solve a different, broader problem (tracking
changes to arbitrary rows over time, with undo/diff support), the actual need here is a
simple, append-only log of one specific event shape, which an off-the-shelf audit
library would not reduce to less code than a single insert function. The real
enforcement of "append-only" is the database grant, see
[0005](0005-separate-app-db-role-for-append-only-audit-log.md), not the writer code.

## Consequences

If the audit log's shape grows (for example, recording retrieval scores or latency),
this function's signature grows with it, by hand, there is no library abstraction doing
that for free. Acceptable for one table with a fixed, known shape.
