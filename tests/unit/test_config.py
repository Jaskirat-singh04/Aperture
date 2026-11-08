"""Unit tests for the configuration module."""

from aperture.config import Settings, get_settings


def test_settings_have_sane_defaults() -> None:
    settings = Settings()
    assert settings.environment == "local"
    assert settings.database.name == "aperture"
    assert settings.llm.model
    assert settings.llm.embedding_model


def test_sqlalchemy_url_is_built_from_parts() -> None:
    settings = Settings()
    url = settings.database.sqlalchemy_url
    assert url.startswith("postgresql+psycopg://")
    assert settings.database.host in url
    assert settings.database.name in url


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
