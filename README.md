# Aperture

A permission-aware knowledge assistant: it answers questions from internal documents,
grounded only in what the asking user is allowed to read, with citations and an audit
log of who asked what.

## Quickstart

Requirements: Python 3.11 or 3.12, [uv](https://docs.astral.sh/uv/), Docker and Docker
Compose.

```bash
make setup   # uv sync, install pre-commit hooks
make up      # start Postgres, OpenFGA, Dex, Ollama and the API, pull the demo models
```

Then, in a separate step (not yet folded into `make up`):

```bash
uv run alembic upgrade head           # create tenants, documents, audit_log tables
uv run python deploy/openfga/seed.py  # write the authorization model and demo tuples
```

Then open the test UI:

```bash
uv run --extra ui streamlit run ui/app.py   # http://localhost:8501
```

Sign in as a demo user (`alice@acme.test`, `bob@acme.test`, or `carol@globex.test`, all
password `password`), ingest a document, and ask a question. alice (tenant acme, group
finance) and bob (tenant acme, group engineering) see different documents, carol (tenant
globex) is fully isolated.

The API is also usable directly. Get a token and call it:

```bash
TOKEN=$(curl -s -X POST http://localhost:5556/dex/token \
  -u "aperture-api:aperture-local-dev-secret" \
  -d grant_type=password -d username=alice@acme.test -d password=password \
  -d scope="openid email groups profile" | python3 -c "import json,sys;print(json.load(sys.stdin)['id_token'])")

curl -s -X POST http://localhost:8000/ingest -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Refund Policy","text":"Enterprise refunds within 30 days.","viewer_groups":["finance"]}'

curl -s -X POST http://localhost:8000/ask -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"question":"What is the refund policy?"}'
```

Run tests and lint:

```bash
make test        # unit tests (no services needed)
make leak-test   # permission-leak tests, needs the stack up + migrated + seeded
make lint        # ruff check, ruff format --check, mypy
```

## Status

Early development. The core permission-aware question-answering flow works end to end
locally, but this is not production ready, and answer quality from the default 1B local
model is modest. Nothing below is a claim about answer quality or production readiness.

**Implemented and working:**

- Local docker compose stack: Postgres with pgvector, OpenFGA (Postgres-backed), Dex
  (local OIDC provider, three seeded demo users), Ollama (self-hosted LLM and
  embeddings), an OTel collector, and the API container.
- OIDC token validation (Authlib, against Dex's JWKS), wired into every endpoint.
- OpenFGA authorization model (tenant, group, user, document) with structural tenant
  isolation (see [ADR 0007](docs/adr/0007-structural-tenant-isolation-in-openfga-model.md)),
  plus a seed script for the demo users and documents.
- Document ingestion (`/ingest`, `/ingest/file`): Docling parses uploaded files,
  LlamaIndex chunks and embeds, pgvector stores chunks with tenant_id/document_id, and
  OpenFGA tuples are written so the document is only retrievable by permitted users.
- Permission-filtered retrieval: OpenFGA resolves the permitted document set before any
  vector query runs, and the pgvector query is restricted to that set and the user's
  tenant.
- Answer generation (`/ask`) via LiteLLM, grounded only in permission-filtered chunks,
  with citations that can never reference a document outside the retrieved set.
- Append-only audit log: every `/ask` writes a record, enforced append-only at the
  database level for the app's role (see [ADR 0005](docs/adr/0005-separate-app-db-role-for-append-only-audit-log.md)).
- Streamlit test UI (`ui/app.py`): sign in as a demo user, ingest, ask, see citations.
- Permission-leak tests (`tests/security/`) run against the live stack as a release gate,
  cross-tenant retrieval, no-access retrieval, and citation leakage all return nothing.
  Verified with zero leaks.
- Tooling: uv, ruff, mypy, pytest, pre-commit, GitHub Actions CI.

**Planned, not implemented:**

- Real source connectors (Google Drive, file shares) that translate source ACLs into
  OpenFGA tuples automatically, ingestion today takes explicit viewer lists.
- OpenTelemetry tracing is stubbed (`aperture.observability.tracing`), not yet wired in.
- Ragas-based answer-quality evals (see `evals/README.md` for the planned format).
- A non-local deployment target (`deploy/terraform-helm-placeholder/` is a placeholder).

See [docs/threat-model.md](docs/threat-model.md) for the risks this design is meant to
resist, and [docs/adr/](docs/adr/) for why the current stack looks the way it does.

## License

Apache License 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE).
