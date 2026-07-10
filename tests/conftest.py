"""Shared test fixtures for weather-friend."""

import pytest

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
