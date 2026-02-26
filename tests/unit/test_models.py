"""Tests for weather_friend.models.weather module."""

import pytest

from weather_friend.models.weather import WeatherData


class TestWeatherData:
    """Tests for the WeatherData dataclass."""

    def test_create_weather_data(self, sample_weather: WeatherData) -> None:
        """Test that WeatherData can be created with valid fields."""
        assert sample_weather.city == "San Jose"
        assert sample_weather.temp_f == 68.0
        assert sample_weather.feels_like_f == 65.0
        assert sample_weather.humidity == 55
        assert sample_weather.description == "scattered clouds"
        assert sample_weather.wind_speed_mph == 8.0
        assert sample_weather.high_f == 74.0
        assert sample_weather.low_f == 58.0
        assert sample_weather.icon == "03d"

    def test_temp_range_summary(self, sample_weather: WeatherData) -> None:
        """Test temp_range_summary formats low-high range correctly."""
        assert sample_weather.temp_range_summary == "58\u00b0F \u2013 74\u00b0F"

    def test_temp_range_summary_rounds_values(self) -> None:
        """Test temp_range_summary rounds fractional temperatures."""
        weather = WeatherData(
            city="Test",
            temp_f=70.0,
            feels_like_f=68.0,
            humidity=50,
            description="clear",
            wind_speed_mph=5.0,
            high_f=75.6,
            low_f=59.4,
            icon="01d",
        )
        assert weather.temp_range_summary == "59\u00b0F \u2013 76\u00b0F"

    def test_frozen_dataclass(self, sample_weather: WeatherData) -> None:
        """Test that WeatherData is immutable (frozen)."""
        with pytest.raises(AttributeError, match="cannot assign"):
            sample_weather.city = "Other City"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Test that two WeatherData with same values are equal."""
        kwargs = {
            "city": "Test",
            "temp_f": 70.0,
            "feels_like_f": 68.0,
            "humidity": 50,
            "description": "clear",
            "wind_speed_mph": 5.0,
            "high_f": 75.0,
            "low_f": 59.0,
            "icon": "01d",
        }
        assert WeatherData(**kwargs) == WeatherData(**kwargs)
