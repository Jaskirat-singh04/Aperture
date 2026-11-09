"""Unit tests for answer generation, with the LLM mocked out."""

from unittest.mock import AsyncMock, MagicMock

from llama_index.core.llms import ChatMessage, ChatResponse, MessageRole

from aperture.generation.service import GenerationService
from aperture.retrieval.service import RetrievedChunk

CHUNKS = [
    RetrievedChunk(document_id="doc-1", text="refunds within 30 days", score=0.9),
    RetrievedChunk(document_id="doc-2", text="enterprise SLAs are 99.9%", score=0.5),
]


def _fake_llm(answer_text: str) -> MagicMock:
    llm = MagicMock()
    llm.achat = AsyncMock(
        return_value=ChatResponse(
            message=ChatMessage(role=MessageRole.ASSISTANT, content=answer_text)
        )
    )
    return llm


async def test_generate_returns_canned_answer_without_calling_llm_when_no_chunks(
    monkeypatch,
) -> None:
    llm = _fake_llm("should not be used")
    monkeypatch.setattr("aperture.generation.service.get_llm", lambda: llm)

    answer = await GenerationService().generate("anything?", [])

    assert answer.cited_document_ids == []
    llm.achat.assert_not_called()


async def test_generate_parses_citations_named_in_the_answer(monkeypatch) -> None:
    llm = _fake_llm("Refunds are given within 30 days [doc-1].")
    monkeypatch.setattr("aperture.generation.service.get_llm", lambda: llm)

    answer = await GenerationService().generate("refund policy?", CHUNKS)

    assert answer.cited_document_ids == ["doc-1"]
    llm.achat.assert_awaited_once()


async def test_generate_falls_back_to_all_retrieved_documents_if_none_cited(
    monkeypatch,
) -> None:
    llm = _fake_llm("Refunds are given within 30 days.")
    monkeypatch.setattr("aperture.generation.service.get_llm", lambda: llm)

    answer = await GenerationService().generate("refund policy?", CHUNKS)

    assert answer.cited_document_ids == ["doc-1", "doc-2"]


async def test_generate_never_cites_a_document_outside_the_retrieved_chunks(
    monkeypatch,
) -> None:
    """Even if the model names a document ID that was never in the
    context, it must not appear in cited_document_ids, see
    tests/security/test_permission_leaks.py.
    """

    llm = _fake_llm("According to [doc-1] and also [doc-does-not-exist], 30 days.")
    monkeypatch.setattr("aperture.generation.service.get_llm", lambda: llm)

    answer = await GenerationService().generate("refund policy?", CHUNKS)

    assert answer.cited_document_ids == ["doc-1"]
    assert "doc-does-not-exist" not in answer.cited_document_ids
