"""The Aperture FastAPI application.

/ingest and /ask are stubbed (501 Not Implemented), the ingestion,
retrieval and generation packages they will call are typed stubs, see
their module docstrings for the intended flow. The OIDC dependency on
both endpoints is real: a caller must present a valid Dex-issued token
before reaching the stub, so permission plumbing can be tested
independently of the features that are not built yet.
"""

from fastapi import Depends, FastAPI

from aperture.api.schemas import AskRequest, HealthResponse, IngestRequest
from aperture.auth import CurrentUser, get_current_user

app = FastAPI(title="Aperture", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/ingest", status_code=501)
async def ingest(
    request: IngestRequest,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    """Not implemented yet. See aperture.ingestion.service for the intended
    flow (parse, chunk, embed and authorize one source document).
    """

    return {"detail": "Ingestion is not implemented yet."}


@app.post("/ask", status_code=501)
async def ask(
    request: AskRequest,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    """Not implemented yet. See aperture.retrieval.service and
    aperture.generation.service for the intended flow (permission-filtered
    retrieval, then generation grounded only in permitted chunks).
    """

    return {"detail": "Ask is not implemented yet."}
