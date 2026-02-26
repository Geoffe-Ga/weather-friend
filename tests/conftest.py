"""Shared test fixtures for weather-friend."""

import pytest

from weather_friend.config import Settings
from weather_friend.models.weather import WeatherData


@pytest.fixture()
def sample_weather() -> WeatherData:
    """Create a sample WeatherData instance for testing."""
    return WeatherData(
        city="San Jose",
        temp_f=68.0,
        feels_like_f=65.0,
        humidity=55,
        description="scattered clouds",
        wind_speed_mph=8.0,
        high_f=74.0,
        low_f=58.0,
        icon="03d",
    )


@pytest.fixture()
def mock_settings() -> Settings:
    """Create a Settings instance with fake credentials for testing."""
    return Settings(
        discord_token="fake-discord-token",
        discord_channel_id=123456789,
        openweather_api_key="fake-weather-key",
        anthropic_api_key="fake-anthropic-key",
    )
