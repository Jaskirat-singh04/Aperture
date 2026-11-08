"""Request and response models for the API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class IngestRequest(BaseModel):
    source_uri: str


class AskRequest(BaseModel):
    question: str
