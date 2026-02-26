"""Tests for weather_friend.config module."""

import pytest

from weather_friend.config import Settings


class TestSettings:
    """Tests for the Settings dataclass."""

    def test_from_env_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Settings.from_env() with all required env vars set."""
        monkeypatch.setenv("DISCORD_TOKEN", "test-token")
        monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
        monkeypatch.setenv("OPENWEATHER_API_KEY", "test-weather-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

        settings = Settings.from_env()

        assert settings.discord_token == "test-token"
        assert settings.discord_channel_id == 123456789
        assert settings.openweather_api_key == "test-weather-key"
        assert settings.anthropic_api_key == "test-anthropic-key"

    def test_from_env_uses_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that from_env() uses default values for optional fields."""
        monkeypatch.setenv("DISCORD_TOKEN", "t")
        monkeypatch.setenv("DISCORD_CHANNEL_ID", "1")
        monkeypatch.setenv("OPENWEATHER_API_KEY", "w")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "a")

        settings = Settings.from_env()

        assert settings.latitude == 37.3382
        assert settings.longitude == -121.8863
        assert settings.city_name == "San Jose"
        assert settings.morning_hour == 7
        assert settings.morning_minute == 0

    def test_from_env_missing_discord_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing DISCORD_TOKEN raises KeyError."""
        monkeypatch.delenv("DISCORD_TOKEN", raising=False)
        monkeypatch.setenv("DISCORD_CHANNEL_ID", "1")
        monkeypatch.setenv("OPENWEATHER_API_KEY", "w")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "a")

        with pytest.raises(KeyError, match="DISCORD_TOKEN"):
            Settings.from_env()

    def test_from_env_missing_channel_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing DISCORD_CHANNEL_ID raises KeyError."""
        monkeypatch.setenv("DISCORD_TOKEN", "t")
        monkeypatch.delenv("DISCORD_CHANNEL_ID", raising=False)
        monkeypatch.setenv("OPENWEATHER_API_KEY", "w")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "a")

        with pytest.raises(KeyError, match="DISCORD_CHANNEL_ID"):
            Settings.from_env()

    def test_from_env_invalid_channel_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that non-integer DISCORD_CHANNEL_ID raises ValueError."""
        monkeypatch.setenv("DISCORD_TOKEN", "t")
        monkeypatch.setenv("DISCORD_CHANNEL_ID", "not-a-number")
        monkeypatch.setenv("OPENWEATHER_API_KEY", "w")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "a")

        with pytest.raises(ValueError, match="invalid literal"):
            Settings.from_env()

    def test_frozen_dataclass(self, mock_settings: Settings) -> None:
        """Test that Settings is immutable (frozen)."""
        with pytest.raises(AttributeError, match="cannot assign"):
            mock_settings.discord_token = "new-token"  # type: ignore[misc]

    def test_direct_construction(self) -> None:
        """Test creating Settings directly with all parameters."""
        settings = Settings(
            discord_token="tok",
            discord_channel_id=42,
            openweather_api_key="key",
            anthropic_api_key="key",
            latitude=40.0,
            longitude=-74.0,
            city_name="New York",
            morning_hour=8,
            morning_minute=30,
        )
        assert settings.city_name == "New York"
        assert settings.morning_hour == 8
        assert settings.morning_minute == 30
