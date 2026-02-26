"""Weather data models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherData:
    """Immutable weather data from OpenWeatherMap.

    Attributes:
        city: City name for the forecast.
        temp_f: Current temperature in Fahrenheit.
        feels_like_f: Feels-like temperature in Fahrenheit.
        humidity: Humidity percentage (0-100).
        description: Human-readable weather description.
        wind_speed_mph: Wind speed in miles per hour.
        high_f: Forecasted high temperature in Fahrenheit.
        low_f: Forecasted low temperature in Fahrenheit.
        icon: OpenWeatherMap icon code (e.g. '01d').
    """

    city: str
    temp_f: float
    feels_like_f: float
    humidity: int
    description: str
    wind_speed_mph: float
    high_f: float
    low_f: float
    icon: str

    @property
    def temp_range_summary(self) -> str:
        """Format the daily temperature range as a human-readable string."""
        return f"{self.low_f:.0f}\u00b0F \u2013 {self.high_f:.0f}\u00b0F"
