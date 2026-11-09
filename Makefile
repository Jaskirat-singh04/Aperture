.PHONY: setup up down test lint leak-test

setup:
	uv sync
	uv run pre-commit install

up:
	docker compose -f deploy/docker-compose.yml up -d --build
	@echo "Pulling Ollama models (llama3.2:1b, nomic-embed-text), first run downloads ~1.5GB..."
	docker compose -f deploy/docker-compose.yml exec ollama ollama pull llama3.2:1b
	docker compose -f deploy/docker-compose.yml exec ollama ollama pull nomic-embed-text

down:
	docker compose -f deploy/docker-compose.yml down

# Unit tests only, no services required. Integration and security tests
# need the docker compose stack (make up) and run as separate CI jobs,
# see .github/workflows/ci.yml.
test:
	uv run pytest tests/unit

# The permission-leak release gate. Runs against the live stack (make up),
# migrations applied, OpenFGA seeded. See docs/threat-model.md and
# tests/security for what these catch. Target is zero leaks.
leak-test:
	uv run pytest tests/security -v

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src
