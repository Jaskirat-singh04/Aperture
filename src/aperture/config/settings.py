"""Application configuration, read from environment variables and .env.

LLM and embedding providers are configured through LiteLLM model identifiers
(for example "openai/gpt-4o-mini" or "ollama/llama3") so swapping a hosted API
for a self-hosted model is a config change, not a code change.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Connection settings for the Postgres instance that holds our own
    tables (tenants, documents, audit_log) and the LlamaIndex pgvector store.

    Two roles are distinguished: "user" is the migration/owner role (runs
    Alembic, owns the tables) and "app_user" is the least-privilege role the
    running application connects as. They are different roles on purpose,
    Postgres table owners bypass GRANT/REVOKE checks, so making audit_log
    append-only only has teeth if the app does not connect as the owner.
    """

    model_config = SettingsConfigDict(env_prefix="APERTURE_DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "aperture"
    user: str = "aperture"
    password: str = "aperture"
    app_user: str = "aperture_app"
    app_password: str = "aperture_app"

    @property
    def sqlalchemy_url(self) -> str:
        """URL for the migration/owner role. Used by Alembic."""
        return (
            f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        )

    @property
    def app_sqlalchemy_url(self) -> str:
        """URL for the least-privilege role the running application uses."""
        return (
            f"postgresql+psycopg://{self.app_user}:{self.app_password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class LLMSettings(BaseSettings):
    """Swappable LLM and embedding provider config, passed through LiteLLM.

    Model identifiers follow the LiteLLM naming convention, so pointing at a
    self-hosted model (for example via Ollama or vLLM) instead of a hosted
    API only requires changing these values.
    """

    model_config = SettingsConfigDict(env_prefix="APERTURE_LLM_")

    model: str = "ollama/llama3"
    embedding_model: str = "ollama/nomic-embed-text"
    api_base: str | None = None
    api_key: str | None = None
    embedding_dimension: int = 768


class OIDCSettings(BaseSettings):
    """Settings for validating tokens issued by the local Dex instance."""

    model_config = SettingsConfigDict(env_prefix="APERTURE_OIDC_")

    issuer: str = "http://localhost:5556/dex"
    audience: str = "aperture-api"
    jwks_url: str = "http://localhost:5556/dex/keys"


class OpenFGASettings(BaseSettings):
    """Settings for the OpenFGA server used for document-level authorization."""

    model_config = SettingsConfigDict(env_prefix="APERTURE_OPENFGA_")

    api_url: str = "http://localhost:8080"
    store_id: str = ""
    authorization_model_id: str = ""


class ObservabilitySettings(BaseSettings):
    """Settings for exporting OpenTelemetry traces to a local collector."""

    model_config = SettingsConfigDict(env_prefix="APERTURE_OTEL_")

    otlp_endpoint: str = "http://localhost:4317"
    service_name: str = "aperture-api"
    enabled: bool = True


class Settings(BaseSettings):
    """Top-level application settings. Nested settings are grouped by concern."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="local")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    oidc: OIDCSettings = Field(default_factory=OIDCSettings)
    openfga: OpenFGASettings = Field(default_factory=OpenFGASettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so settings are read from the environment once per process, not
    on every request.
    """

    return Settings()
