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
        """Fetch current weather data for the configured coordinates.

        Returns:
            A WeatherData instance with the current conditions.

        Raises:
            httpx.HTTPStatusError: If the API returns an error status.
            httpx.RequestError: If the request fails due to network issues.
        """
        params: dict[str, str | float] = {
            "lat": self.lat,
            "lon": self.lon,
            "appid": self._api_key,
            "units": "imperial",
        }
        data = await self._fetch(params)
        return self._build_weather_data(data, city=self.city)

    async def get_weather_for_location(self, location: str) -> WeatherData:
        """Fetch current weather data for an arbitrary location string.

        Args:
            location: Free-form location query, e.g. "Portland,OR".

        Returns:
            A WeatherData instance with the current conditions. The city
            name comes from the API response when available, otherwise
            the requested location string.

        Raises:
            ValueError: If the API does not recognize the location.
            httpx.HTTPStatusError: If the API returns any other error status.
            httpx.RequestError: If the request fails due to network issues.
        """
        params: dict[str, str | float] = {
            "q": location,
            "appid": self._api_key,
            "units": "imperial",
        }
        try:
            data = await self._fetch(params)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == httpx.codes.NOT_FOUND:
                msg = f"unknown location: {location}"
                raise ValueError(msg) from exc
            raise
        city = str(data.get("name") or location)
        return self._build_weather_data(data, city=city)

    async def _fetch(self, params: dict[str, str | float]) -> dict:
        """Call the OpenWeatherMap API and return the parsed JSON body.

        Args:
            params: Query parameters for the current-weather endpoint.

        Returns:
            The decoded JSON response.

        Raises:
            httpx.HTTPStatusError: If the API returns an error status.
            httpx.RequestError: If the request fails due to network issues.
        """
        # OWM requires the API key as a query param (not a header);
        # this is an upstream API constraint. HTTPS is enforced by BASE_URL.
        try:
            async with httpx.AsyncClient(
                timeout=_REQUEST_TIMEOUT,
            ) as client:
                response = await client.get(BASE_URL, params=params)
                response.raise_for_status()
                data: dict = response.json()
        except httpx.HTTPStatusError:
            logger.exception("Weather API HTTP error")
            raise
        except httpx.RequestError:
            logger.exception("Weather API request failed")
            raise
        return data

    @staticmethod
    def _build_weather_data(data: dict, *, city: str) -> WeatherData:
        """Map an OpenWeatherMap response body onto the WeatherData model.

        Args:
            data: Decoded current-weather JSON response.
            city: Display name to attach to the result.

        Returns:
            A populated WeatherData instance.
        """
        main = data["main"]
        weather = data["weather"][0]
        wind = data["wind"]

        return WeatherData(
            city=city,
            temp_f=float(main["temp"]),
            feels_like_f=float(main["feels_like"]),
            humidity=int(main["humidity"]),
            description=str(weather["description"]),
            wind_speed_mph=float(wind["speed"]),
            high_f=float(main["temp_max"]),
            low_f=float(main["temp_min"]),
            icon=str(weather["icon"]),
        )
