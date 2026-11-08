# Aperture

A permission-aware knowledge assistant: it answers questions from internal documents,
grounded only in what the asking user is allowed to read, with citations and an audit
log of who asked what.

## Quickstart

Requirements: Python 3.11 or 3.12, [uv](https://docs.astral.sh/uv/), Docker and Docker
Compose.

```bash
make setup   # uv sync, install pre-commit hooks
make up      # start Postgres, OpenFGA, Dex and the API
```

Then, in a separate step (not yet folded into `make up`):

```bash
uv run alembic upgrade head           # create tenants, documents, audit_log tables
uv run python deploy/openfga/seed.py  # write the authorization model and demo tuples
```

Demo users (seeded in Dex, see `deploy/dex/config.yaml`): `alice@acme.test`,
`bob@acme.test`, `carol@globex.test`, all with password `password`. Get a token:

```bash
curl -s -X POST http://localhost:5556/dex/token \
  -u "aperture-api:aperture-local-dev-secret" \
  -d grant_type=password -d username=alice@acme.test -d password=password \
  -d scope="openid email groups profile"
```

Check the API is up:

```bash
curl http://localhost:8000/health
```

Run tests and lint:

```bash
make test   # unit and security tests (security tests are mostly skipped for now)
make lint   # ruff check, ruff format --check, mypy
```

## Status

Early development. Ingestion, retrieval and generation are not implemented yet, so
asking a real question does not work yet, `/ask` returns 501. Nothing below is a claim
about answer quality or production readiness.

**Implemented:**

- Repo and tooling: uv, ruff, mypy, pytest, pre-commit, GitHub Actions CI.
- Local docker compose stack: Postgres with pgvector, OpenFGA (Postgres-backed), Dex
  (local OIDC provider, three seeded demo users), an OTel collector, and the API
  container. Verified to start and respond to `/health`.
- Database schema (`tenants`, `documents`, `audit_log`) via Alembic, with `audit_log`
  enforced append-only at the database level for the app's role (verified by
  integration tests, see [ADR 0005](docs/adr/0005-separate-app-db-role-for-append-only-audit-log.md)).
- OpenFGA authorization model (tenant, group, user, document) with structural tenant
  isolation, plus a seed script for the three demo users and sample documents. Verified
  against a live OpenFGA instance for direct access, group access, and cross-tenant
  denial, including the case where two tenants have a same-named group.
- OIDC token validation (Authlib, against Dex's JWKS), wired into the API as a FastAPI
  dependency on every endpoint.
- Append-only audit log writer (plain SQLAlchemy insert).
- `/health` endpoint (real). `/ingest` and `/ask` endpoints exist, require a valid
  token, and return 501 (not implemented).

**Planned, not implemented:**

- Document ingestion: parsing with Docling, chunking and embedding with LlamaIndex,
  writing to the pgvector store, translating source ACLs into OpenFGA tuples.
- Permission-filtered retrieval: resolving a user's permitted documents via OpenFGA
  before any vector query runs.
- Answer generation via LiteLLM, grounded only in permission-filtered chunks, with
  citations.
- The permission-leak tests in `tests/security/` are written but skipped, they become a
  real release gate once retrieval and generation exist and these tests are un-skipped
  and passing.
- Ragas-based answer-quality evals (see `evals/README.md` for the planned format).
- A non-local deployment target (`deploy/terraform-helm-placeholder/` is an empty
  placeholder).

See [docs/threat-model.md](docs/threat-model.md) for the risks this design is meant to
resist, and [docs/adr/](docs/adr/) for why the current stack looks the way it does.

## License

Apache License 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE).
