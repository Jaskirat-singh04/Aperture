# 0002: Docling For Document Parsing

## Status

Accepted.

## Context

Ingestion needs to parse heterogeneous source documents (PDFs, Office documents, HTML)
into clean, structured text before chunking. Docling and Unstructured both do this, and
both are realistic choices:

- Docling (`docling-project/docling`): MIT license, backed by IBM and the LF AI & Data
  Foundation, actively released. Ships layout and OCR models that run fully locally
  (CPU-only wheels are used here, see
  [0009](0009-cpu-only-torch-wheels.md)). Has first-party LlamaIndex integration
  (`llama-index-readers-docling`, `llama-index-node-parser-docling`).
- Unstructured (`Unstructured-IO/unstructured`): Apache 2.0 license, also actively
  maintained, open source core works locally, best results for some document types are
  steered toward their hosted API.

## Decision

Use Docling.

Both licenses are acceptable (MIT and Apache 2.0 are both on the permissive allow list).
Docling's local-first design fits hard requirement 4 (no cloud accounts, runs fully
locally) a little more directly, and its first-party LlamaIndex integration means less
custom glue code to parse Docling's output into LlamaIndex documents and chunks.

## Consequences

Docling pulls in `torch` and `torchvision` transitively (for layout and OCR models),
pinned to CPU-only wheels, see
[0009-cpu-only-torch-wheels.md](0009-cpu-only-torch-wheels.md). If a document type
parses poorly with Docling, Unstructured remains an option to add alongside it later,
the ingestion package's stub does not assume Docling is the only possible parser.
