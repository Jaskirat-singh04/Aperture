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

# Unit and security tests only, no services required. Integration tests
# need the docker compose stack (make up) and run as a separate CI job,
# see .github/workflows/ci.yml.
test:
	uv run pytest tests/unit tests/security

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src

# Mirrors the CI "permission-leak-tests" job, see docs/threat-model.md and
# tests/security for what these are meant to catch.
leak-test:
	uv run pytest tests/security -v
