"""The Aperture FastAPI application.

/ingest and /ask require a valid Dex-issued OIDC token, then call the
ingestion, retrieval and generation services in turn. Permissions are
always resolved from the token (CurrentUser), never from request input,
tenant_id and groups cannot be spoofed by a client.
"""

from fastapi import Depends, FastAPI, File, Form, UploadFile
from sqlalchemy.orm import Session

from aperture.api.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
)
from aperture.audit import record_query
from aperture.auth import CurrentUser, get_current_user
from aperture.db import get_session
from aperture.generation import GenerationService
from aperture.ingestion import IngestionService
from aperture.retrieval import RetrievalService

app = FastAPI(title="Aperture", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    request: IngestRequest,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> IngestResponse:
    """Ingest already-extracted text into the caller's own tenant."""

    service = IngestionService(session)
    result = await service.ingest_text(
        tenant_id=user.tenant_id,
        title=request.title,
        text=request.text,
        direct_viewers=request.direct_viewers,
        viewer_groups=request.viewer_groups,
    )
    session.commit()
    return IngestResponse(document_id=result.document_id, chunk_count=result.chunk_count)


@app.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    direct_viewers: str = Form(""),
    viewer_groups: str = Form(""),
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> IngestResponse:
    """Ingest an uploaded file (PDF, DOCX, HTML, ...), parsed with Docling.

    direct_viewers and viewer_groups are comma-separated, form fields do
    not carry JSON arrays.
    """

    service = IngestionService(session)
    result = await service.ingest_file(
        tenant_id=user.tenant_id,
        title=title,
        filename=file.filename or title,
        content=await file.read(),
        direct_viewers=[v.strip() for v in direct_viewers.split(",") if v.strip()],
        viewer_groups=[v.strip() for v in viewer_groups.split(",") if v.strip()],
    )
    session.commit()
    return IngestResponse(document_id=result.document_id, chunk_count=result.chunk_count)


@app.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AskResponse:
    """Answer a question, grounded only in documents `user` may read."""

    chunks = await RetrievalService().retrieve(user, request.question)
    answer = await GenerationService().generate(request.question, chunks)

    record_query(
        session,
        tenant_id=user.tenant_id,
        user_id=user.subject,
        question=request.question,
        document_ids_used=answer.cited_document_ids,
    )
    session.commit()

    return AskResponse(answer=answer.text, cited_document_ids=answer.cited_document_ids)
