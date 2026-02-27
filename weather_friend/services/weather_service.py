"""Fetches weather data from OpenWeatherMap API."""

import logging

import httpx

from weather_friend.models.weather import WeatherData

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
_REQUEST_TIMEOUT = 10.0


class WeatherService:
    """Service for retrieving current weather data from OpenWeatherMap.

    Attributes:
        lat: Latitude for the weather query.
        lon: Longitude for the weather query.
        city: Display name for the city.
    """

    def __init__(self, api_key: str, lat: float, lon: float, city: str) -> None:
        """Initialize the weather service.

        Args:
            api_key: OpenWeatherMap API key.
            lat: Latitude for the weather query.
            lon: Longitude for the weather query.
            city: Display name for the city.
        """
        self._api_key = api_key
        self.lat = lat
        self.lon = lon
        self.city = city

    async def get_current_weather(self) -> WeatherData:
        """Fetch current weather data from OpenWeatherMap.

        Returns:
            A WeatherData instance with the current conditions.

        Raises:
            httpx.HTTPStatusError: If the API returns an error status.
            httpx.RequestError: If the request fails due to network issues.
        """
        # OWM requires the API key as a query param (not a header);
        # this is an upstream API constraint. HTTPS is enforced by BASE_URL.
        params: dict[str, str | float] = {
            "lat": self.lat,
            "lon": self.lon,
            "appid": self._api_key,
            "units": "imperial",
        }
        try:
            async with httpx.AsyncClient(
                timeout=_REQUEST_TIMEOUT,
            ) as client:
                response = await client.get(BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError:
            logger.exception("Weather API HTTP error")
            raise
        except httpx.RequestError:
            logger.exception("Weather API request failed")
            raise

        main = data["main"]
        weather = data["weather"][0]
        wind = data["wind"]

        return WeatherData(
            city=self.city,
            temp_f=float(main["temp"]),
            feels_like_f=float(main["feels_like"]),
            humidity=int(main["humidity"]),
            description=str(weather["description"]),
            wind_speed_mph=float(wind["speed"]),
            high_f=float(main["temp_max"]),
            low_f=float(main["temp_min"]),
            icon=str(weather["icon"]),
        )
