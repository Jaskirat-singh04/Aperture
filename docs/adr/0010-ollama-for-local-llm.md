# 0010: Ollama For The Local LLM And Embedding Provider

## Status

Accepted.

## Context

Hard requirement 4 is that the whole project runs locally with no cloud
accounts, and requirement 5 is that the LLM and embedding provider are
swappable through config. LiteLLM already gives the swappable-provider
abstraction, but something has to actually serve a model locally for the
default, out-of-the-box experience.

## Decision

Add Ollama as a docker compose service, with `llama3.2:1b` (chat) and
`nomic-embed-text` (embeddings) as the defaults. LiteLLM talks to it via its
`ollama/<model>` provider prefix and `APERTURE_LLM_API_BASE`, so pointing at
a hosted provider (OpenAI, Anthropic, ...) instead is still just changing
`APERTURE_LLM_MODEL` / `APERTURE_LLM_API_KEY`, no code change.

`llama3.2:1b` is deliberately small: it runs at a usable speed on CPU (there
is no GPU passthrough in the default local setup), which matters more for a
testable default than answer quality. Models are pulled by `make up` after
the container starts, not baked into any image.

## Consequences

The first `make up` downloads roughly 1.5 GB of model weights, and answer
quality from a 1B model is modest. Both are acceptable for a local
development and testing default, a real deployment would point LiteLLM at a
larger self-hosted model or a hosted API by changing config only.
