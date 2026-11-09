"""Permission-aware retrieval: resolve permitted documents before any
vector query runs.
"""

from aperture.retrieval.service import DEFAULT_TOP_K, RetrievalService, RetrievedChunk

__all__ = ["DEFAULT_TOP_K", "RetrievalService", "RetrievedChunk"]
