"""Tests for weather_friend.config module."""

import pytest

from weather_friend.config import (
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    DEFAULT_CITY_NAME,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    ApiSettings,
)


class TestApiSettings:
    """Tests for the ApiSettings dataclass (construction semantics).

    ``from_env`` behavior is covered in tests/test_api_entrypoint.py.
    """

    def test_direct_construction_uses_defaults(self) -> None:
        """Test that optional fields default to San Jose on localhost:8002."""
        settings = ApiSettings(
            openweather_api_key="w",
            anthropic_api_key="a",
        )
        assert settings.host == DEFAULT_API_HOST
        assert settings.port == DEFAULT_API_PORT
        assert settings.latitude == DEFAULT_LATITUDE
        assert settings.longitude == DEFAULT_LONGITUDE
        assert settings.city_name == DEFAULT_CITY_NAME

    def test_direct_construction_with_overrides(self) -> None:
        """Test creating ApiSettings directly with all parameters."""
        settings = ApiSettings(
            openweather_api_key="w",
            anthropic_api_key="a",
            host="127.0.0.2",
            port=9000,
            latitude=40.0,
            longitude=-74.0,
            city_name="New York",
        )
        assert settings.host == "127.0.0.2"
        assert settings.port == 9000
        assert settings.city_name == "New York"

    def test_frozen_dataclass(self) -> None:
        """Test that ApiSettings is immutable (frozen)."""
        settings = ApiSettings(
            openweather_api_key="w",
            anthropic_api_key="a",
        )
        with pytest.raises(AttributeError, match="cannot assign"):
            settings.port = 9000  # type: ignore[misc]
