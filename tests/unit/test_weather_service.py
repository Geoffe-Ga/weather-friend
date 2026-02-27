"""Tests for weather_friend.services.weather_service module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from weather_friend.services.weather_service import WeatherService


def _make_service() -> WeatherService:
    """Create a WeatherService with fake credentials."""
    return WeatherService(
        api_key="fake-key", lat=37.3382, lon=-121.8863, city="San Jose"
    )


def _sample_api_response() -> dict:
    """Return a sample OpenWeatherMap API response."""
    return {
        "main": {
            "temp": 68.0,
            "feels_like": 65.0,
            "humidity": 55,
            "temp_max": 74.0,
            "temp_min": 58.0,
        },
        "weather": [{"description": "scattered clouds", "icon": "03d"}],
        "wind": {"speed": 8.0},
    }


class TestWeatherService:
    """Tests for the WeatherService class."""

    def test_init_stores_params(self) -> None:
        """Test that constructor stores all parameters."""
        service = _make_service()
        assert service._api_key == "fake-key"
        assert service.lat == 37.3382
        assert service.lon == -121.8863
        assert service.city == "San Jose"

    def test_api_key_is_private(self) -> None:
        """Test that the API key is stored as a private attribute."""
        service = _make_service()
        assert not hasattr(service, "api_key")
        assert hasattr(service, "_api_key")

    @pytest.mark.asyncio()
    async def test_get_current_weather_success(self) -> None:
        """Test successful weather fetch returns correct WeatherData."""
        service = _make_service()
        mock_response = MagicMock()
        mock_response.json.return_value = _sample_api_response()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "weather_friend.services.weather_service.httpx.AsyncClient",
            return_value=mock_client,
        ):
            weather = await service.get_current_weather()

        assert weather.city == "San Jose"
        assert weather.temp_f == 68.0
        assert weather.feels_like_f == 65.0
        assert weather.humidity == 55
        assert weather.description == "scattered clouds"
        assert weather.wind_speed_mph == 8.0
        assert weather.high_f == 74.0
        assert weather.low_f == 58.0
        assert weather.icon == "03d"

    @pytest.mark.asyncio()
    async def test_get_current_weather_sends_correct_params(self) -> None:
        """Test that the API call includes correct query parameters."""
        service = _make_service()
        mock_response = MagicMock()
        mock_response.json.return_value = _sample_api_response()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "weather_friend.services.weather_service.httpx.AsyncClient",
            return_value=mock_client,
        ):
            await service.get_current_weather()

        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["lat"] == 37.3382
        assert params["lon"] == -121.8863
        assert params["appid"] == "fake-key"
        assert params["units"] == "imperial"

    @pytest.mark.asyncio()
    async def test_get_current_weather_uses_explicit_timeout(self) -> None:
        """Test that the httpx client is created with an explicit timeout."""
        service = _make_service()
        mock_response = MagicMock()
        mock_response.json.return_value = _sample_api_response()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "weather_friend.services.weather_service.httpx.AsyncClient",
            return_value=mock_client,
        ) as mock_constructor:
            await service.get_current_weather()

        mock_constructor.assert_called_once_with(timeout=10.0)

    @pytest.mark.asyncio()
    async def test_get_current_weather_http_error(self) -> None:
        """Test that HTTP errors are re-raised."""
        service = _make_service()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "weather_friend.services.weather_service.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await service.get_current_weather()

    @pytest.mark.asyncio()
    async def test_get_current_weather_request_error(self) -> None:
        """Test that network errors are re-raised."""
        service = _make_service()

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "weather_friend.services.weather_service.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(httpx.RequestError),
        ):
            await service.get_current_weather()
