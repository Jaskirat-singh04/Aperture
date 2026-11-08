"""Answer generation.

Not implemented yet. Intended flow:

1. Take the chunks returned by retrieval.RetrievalService.retrieve (already
   filtered to documents the asking user may read).
2. Build a prompt that includes the chunk text and source document IDs, and
   call the configured LLM through LiteLLM (model from Settings.llm.model),
   so swapping a hosted provider for a self-hosted one is a config change.
3. Return an answer with citations, where every cited document ID must be
   one of the document IDs passed in from retrieval. A citation to a
   document outside that set is a bug, not a formatting detail, and should
   be filtered out or raise rather than silently rendered.

This module never queries the vector store or OpenFGA directly, it only
ever sees chunks that retrieval has already permission-filtered.
"""

from dataclasses import dataclass

from aperture.retrieval.service import RetrievedChunk


@dataclass
class Answer:
    """A generated answer with citations back to source documents."""

    text: str
    cited_document_ids: list[str]


class GenerationService:
    """Stub. See module docstring for the intended flow."""

    async def generate(self, question: str, chunks: list[RetrievedChunk]) -> Answer:
        """Generate an answer to `question` grounded only in `chunks`.

        TODO: call the configured LiteLLM model and build citations only
        from the document IDs present in `chunks`.
        """

        raise NotImplementedError("Answer generation is not implemented yet.")
