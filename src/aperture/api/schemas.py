"""Request and response models for the API."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class IngestRequest(BaseModel):
    """Ingest already-extracted text. Always into the caller's own tenant,
    tenant_id is taken from the authenticated user, never from the request.
    """

    title: str
    text: str
    direct_viewers: list[str] = Field(default_factory=list)
    viewer_groups: list[str] = Field(default_factory=list)


class IngestResponse(BaseModel):
    document_id: str
    chunk_count: int


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    cited_document_ids: list[str]
