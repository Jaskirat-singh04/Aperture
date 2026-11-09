"""Answer generation, grounded only in permission-filtered chunks.

This module never queries the vector store or OpenFGA directly, it only
ever sees chunks that aperture.retrieval.service has already permission
filtered. The returned citations are always a subset of the document IDs
those chunks came from, by construction, see _extract_citations below, a
citation to a document outside that set is treated as a bug and dropped,
not rendered.
"""

import re
from dataclasses import dataclass

from llama_index.core.llms import ChatMessage, MessageRole

from aperture.retrieval.service import RetrievedChunk
from aperture.vector_store import get_llm

_CITATION_PATTERN = re.compile(r"\[(doc-[A-Za-z0-9_-]+)\]")

_SYSTEM_PROMPT = (
    "You are Aperture, an internal knowledge assistant. Answer the question "
    "using ONLY the context below, each taken from one source document. If "
    "the context does not answer the question, say you do not know, do not "
    "use outside knowledge. After every fact you state, cite the document "
    "it came from in square brackets, for example [doc-acme-finance-policy]."
)

_NO_CONTEXT_ANSWER = (
    "I don't have any documents you're permitted to read that look relevant to this question."
)


@dataclass
class Answer:
    """A generated answer with citations back to source documents."""

    text: str
    cited_document_ids: list[str]


def _build_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[{chunk.document_id}]\n{chunk.text}" for chunk in chunks)


def _extract_citations(answer_text: str, permitted_document_ids: set[str]) -> list[str]:
    """Citations named in the answer text, restricted to permitted_document_ids.

    Falls back to all of permitted_document_ids if the model did not name
    any (common for small local models), so the audit log still reflects
    which documents were actually used to answer the question.
    """

    named = {
        match for match in _CITATION_PATTERN.findall(answer_text) if match in permitted_document_ids
    }
    return sorted(named) if named else sorted(permitted_document_ids)


class GenerationService:
    async def generate(self, question: str, chunks: list[RetrievedChunk]) -> Answer:
        """Generate an answer to `question` grounded only in `chunks`."""

        if not chunks:
            return Answer(text=_NO_CONTEXT_ANSWER, cited_document_ids=[])

        context = _build_context(chunks)
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=_SYSTEM_PROMPT),
            ChatMessage(
                role=MessageRole.USER, content=f"Context:\n{context}\n\nQuestion: {question}"
            ),
        ]

        response = await get_llm().achat(messages)
        answer_text = response.message.content or ""

        permitted_document_ids = {chunk.document_id for chunk in chunks}
        cited_document_ids = _extract_citations(answer_text, permitted_document_ids)

        return Answer(text=answer_text, cited_document_ids=cited_document_ids)
