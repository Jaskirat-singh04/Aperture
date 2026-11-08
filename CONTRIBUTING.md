# Contributing To Aperture

Aperture is a solo-maintained, early-stage project. Contributions are welcome, but keep
changes small and focused, this project deliberately favors existing libraries over new
custom code, see the ADRs in [docs/adr/](docs/adr/) for the reasoning behind the current
stack.

## Development Setup

Requirements: Python 3.11 or 3.12, [uv](https://docs.astral.sh/uv/), Docker and Docker
Compose.

```bash
make setup   # uv sync, install pre-commit hooks
make up      # start Postgres, OpenFGA, Dex and the API
make test    # unit and security tests (security tests are mostly skipped for now)
make lint    # ruff check, ruff format --check, mypy
```

Unit and security tests do not need the docker compose stack. Integration tests
(`tests/integration/`) do, run them after `make up` with:

```bash
uv run pytest tests/integration -m integration
```

## Before Opening A Pull Request

- Run `make lint` and `make test`, both must pass.
- If you change a dependency, update `uv.lock` (`uv lock`) and check
  `uv run python scripts/check_licenses.py` still passes (no GPL or AGPL dependencies).
- If you touch anything in `tests/security/`, explain in the PR description what leak
  scenario it covers and why it is safe to un-skip (if applicable).
- Keep commits small and use
  [Conventional Commits](https://www.conventionalcommits.org/) style messages (for example
  `feat(retrieval): ...`, `fix(auth): ...`, `docs: ...`).

## Code Style

- Python, formatted and linted with ruff (`ruff format`, `ruff check`), type checked with
  mypy in non-strict mode (see `pyproject.toml` for why).
- No em dashes in code, comments or docs. Use commas, periods or parentheses instead.
- Markdown headings use title case.
- Comment code only where it needs clarification, not as a narration of what the code
  already says.

## Design Principle

Before writing custom code, check whether an existing, actively maintained library already
does it. Only permissively licensed dependencies are accepted (Apache 2.0, MIT, BSD), with
the single documented exception of LGPL for `psycopg`, see
[docs/adr/0004-psycopg-lgpl-dependency.md](docs/adr/0004-psycopg-lgpl-dependency.md).
GPL and AGPL dependencies are rejected outright and checked for in CI.
