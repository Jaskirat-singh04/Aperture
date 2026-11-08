# 0009: Pin Torch And Torchvision To CPU-Only Wheels

## Status

Accepted.

## Context

Docling (via `docling-ibm-models`) depends on `torch` and `torchvision` for its layout
and OCR models. On Linux, PyPI's default `torch` wheel pulls in a full set of NVIDIA CUDA
packages (`nvidia-cublas`, `nvidia-cufft`, `nvidia-cudnn`, and others), several GB, none
of which this project uses: LLM inference goes through LiteLLM to a hosted API or a
separately run self-hosted model (hard requirement 5), never through local GPU
inference in the API container.

## Decision

Pin `torch` and `torchvision` as direct dependencies (not just transitive, via Docling)
and redirect them to PyTorch's CPU-only wheel index in `pyproject.toml`:

```toml
[tool.uv.sources]
torch = { index = "pytorch-cpu" }
torchvision = { index = "pytorch-cpu" }

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

uv only honors a source override for a package declared directly in
`[project.dependencies]`, which is why both are pinned directly even though Docling
already requires them transitively.

## Consequences

Verified: this removes `cuda-bindings`, `cuda-toolkit` and all `nvidia-*` packages from
`uv.lock`, and cuts the API container's Docker build from several minutes (downloading
GB of CUDA packages) to under two. If GPU-accelerated local parsing is ever wanted, this
override would need to be removed or made platform-conditional.
