"""Tracing is not wired up yet, see aperture.observability.tracing."""

import pytest

from aperture.observability import configure_tracing


@pytest.mark.skip(
    reason="OpenTelemetry tracing is not wired up yet, see aperture.observability.tracing"
)
def test_configure_tracing_instruments_the_app_and_exports_to_collector() -> None:
    """Expected behavior once implemented: configure_tracing registers a
    TracerProvider exporting spans via OTLP to the configured collector
    endpoint, and the FastAPI app (aperture.api.main.app) is instrumented
    so every request produces a span.
    """


def test_configure_tracing_raises_for_now() -> None:
    with pytest.raises(NotImplementedError):
        configure_tracing(service_name="aperture-api", otlp_endpoint="http://localhost:4317")
