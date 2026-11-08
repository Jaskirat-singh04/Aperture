"""OpenTelemetry tracing.

Not implemented yet. Intended setup, once there is request/retrieval/
generation logic worth tracing:

1. Build a TracerProvider with an OTLP exporter pointed at
   Settings.observability.otlp_endpoint (the local collector started by
   docker compose, see deploy/otel/otel-collector-config.yaml).
2. Instrument the FastAPI app with
   opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.
3. Add explicit spans around the retrieval and generation steps, since the
   permission boundary (OpenFGA check, then vector query) is exactly the
   kind of thing worth being able to see in a trace: span attributes should
   include tenant_id and the count of permitted document IDs, never raw
   document content.

Not wired into the FastAPI app yet (see aperture.api.main), there is no
retrieval or generation to trace until those are implemented.
"""


def configure_tracing(service_name: str, otlp_endpoint: str) -> None:
    """TODO: build and register a TracerProvider exporting to otlp_endpoint,
    then instrument the FastAPI app in aperture.api.main.
    """

    raise NotImplementedError("OpenTelemetry tracing is not wired up yet.")
