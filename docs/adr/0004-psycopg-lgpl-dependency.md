# 0004: Psycopg Is An Accepted LGPL Exception

## Status

Accepted.

## Context

The stated dependency policy is permissive licenses only (Apache 2.0, MIT, BSD), GPL and
AGPL rejected outright. `psycopg` (the Postgres driver SQLAlchemy and Alembic connect
through) is licensed LGPL-3.0, which is neither on the permissive allow list nor GPL or
AGPL.

LGPL's linking exception means code that merely uses (imports, links against) an LGPL
library is not itself required to be LGPL or open source, only modifications to the
LGPL library itself carry that obligation. This is why `psycopg`/`psycopg2` has been the
de facto standard Postgres driver for two decades, used from proprietary and
permissively licensed codebases alike, without controversy.

## Decision

Accept `psycopg` (LGPL-3.0) as a documented exception to the "permissive licenses only"
rule. It is not GPL or AGPL, which are the licenses this project actually needs to avoid
for its own obligations, and it is the actively maintained, first-class driver for
SQLAlchemy and Alembic.

`scripts/check_licenses.py` (the CI license gate) checks for GPL and AGPL specifically,
and does not flag LGPL, so this exception does not require an extra allowlist entry
to maintain.

## Consequences

If a stricter license policy is adopted later (no LGPL at all), the practical
alternative is `asyncpg` (Apache 2.0), which would need separate sync support for
Alembic (`asyncpg` is async-only) or a switch to `pg8000` (BSD, pure Python, slower).
Not changed now because the current policy explicitly targets GPL/AGPL, not LGPL.
