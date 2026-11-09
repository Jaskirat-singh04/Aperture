"""Unit tests for permission-aware retrieval, with OpenFGA and the vector
store mocked out. See tests/integration for the real-stack version.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryResult

from aperture.auth.models import CurrentUser
from aperture.retrieval.service import RetrievalService

ALICE = CurrentUser(subject="alice", tenant_id="acme", groups=["finance"])


def _fake_openfga_client(objects: list[str]):
    client = MagicMock()
    client.list_objects = AsyncMock(return_value=MagicMock(objects=objects))

    @asynccontextmanager
    async def _ctx():
        yield client

    return _ctx, client


async def test_list_permitted_document_ids_strips_type_prefix(monkeypatch) -> None:
    ctx, _ = _fake_openfga_client(["document:doc-1", "document:doc-2"])
    monkeypatch.setattr("aperture.retrieval.service.get_openfga_client", ctx)

    service = RetrievalService()
    ids = await service.list_permitted_document_ids(ALICE)

    assert ids == ["doc-1", "doc-2"]


async def test_retrieve_returns_empty_without_querying_vector_store_when_no_access(
    monkeypatch,
) -> None:
    ctx, _ = _fake_openfga_client([])
    monkeypatch.setattr("aperture.retrieval.service.get_openfga_client", ctx)

    vector_store = MagicMock()
    vector_store.aquery = AsyncMock()
    monkeypatch.setattr("aperture.retrieval.service.get_vector_store", lambda: vector_store)

    chunks = await RetrievalService().retrieve(ALICE, "anything?")

    assert chunks == []
    vector_store.aquery.assert_not_called()


async def test_retrieve_restricts_query_to_permitted_documents_and_tenant(
    monkeypatch,
) -> None:
    ctx, _ = _fake_openfga_client(["document:doc-1"])
    monkeypatch.setattr("aperture.retrieval.service.get_openfga_client", ctx)

    embed_model = MagicMock()
    embed_model.aget_query_embedding = AsyncMock(return_value=[0.1, 0.2])
    monkeypatch.setattr("aperture.retrieval.service.get_embed_model", lambda: embed_model)

    node = TextNode(text="refunds within 30 days", metadata={"document_id": "doc-1"})
    query_result = VectorStoreQueryResult(nodes=[node], similarities=[0.87])
    vector_store = MagicMock()
    vector_store.aquery = AsyncMock(return_value=query_result)
    monkeypatch.setattr("aperture.retrieval.service.get_vector_store", lambda: vector_store)

    chunks = await RetrievalService().retrieve(ALICE, "refund policy?")

    assert len(chunks) == 1
    assert chunks[0].document_id == "doc-1"
    assert chunks[0].score == pytest.approx(0.87)

    query = vector_store.aquery.call_args[0][0]
    filter_keys_and_values = {
        (f.key, tuple(f.value) if isinstance(f.value, list) else f.value)
        for f in query.filters.filters
    }
    assert ("document_id", ("doc-1",)) in filter_keys_and_values
    assert ("tenant_id", "acme") in filter_keys_and_values
