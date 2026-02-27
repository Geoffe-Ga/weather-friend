"""Tests for weather_friend.services.message_service module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from weather_friend.models.weather import WeatherData
from weather_friend.services.message_service import (
    CLAUDE_MODEL,
    ORACLE_SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    MessageService,
)


def _sample_weather() -> WeatherData:
    """Create a sample WeatherData for testing."""
    return WeatherData(
        city="San Jose",
        temp_f=68.0,
        feels_like_f=65.0,
        humidity=55,
        description="clear sky",
        wind_speed_mph=5.0,
        high_f=74.0,
        low_f=58.0,
        icon="01d",
    )


class TestMessageService:
    """Tests for the MessageService class."""

    @pytest.mark.asyncio()
    async def test_generate_forecast_calls_claude_api(self) -> None:
        """Test that generate_forecast_message calls Claude with correct params."""
        mock_text_block = MagicMock()
        mock_text_block.text = "The stars whisper of warmth today."
        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        with patch(
            "weather_friend.services.message_service.anthropic.AsyncAnthropic",
            return_value=mock_client,
        ):
            service = MessageService(api_key="fake-key")
            service.client = mock_client
            message = await service.generate_forecast_message(_sample_weather())

        assert "The stars whisper of warmth today." in message
        mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio()
    async def test_generate_forecast_uses_correct_model(self) -> None:
        """Test that the service calls the correct Claude model."""
        mock_text_block = MagicMock()
        mock_text_block.text = "Forecast text"
        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        with patch(
            "weather_friend.services.message_service.anthropic.AsyncAnthropic",
            return_value=mock_client,
        ):
            service = MessageService(api_key="fake-key")
            service.client = mock_client
            await service.generate_forecast_message(_sample_weather())

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == CLAUDE_MODEL
        assert call_kwargs["max_tokens"] == 300
        assert call_kwargs["system"] == ORACLE_SYSTEM_PROMPT

    @pytest.mark.asyncio()
    async def test_generate_forecast_formats_user_prompt(self) -> None:
        """Test that weather data is formatted into the user prompt."""
        mock_text_block = MagicMock()
        mock_text_block.text = "Forecast"
        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        with patch(
            "weather_friend.services.message_service.anthropic.AsyncAnthropic",
            return_value=mock_client,
        ):
            service = MessageService(api_key="fake-key")
            service.client = mock_client
            await service.generate_forecast_message(_sample_weather())

        call_kwargs = mock_client.messages.create.call_args.kwargs
        user_content = call_kwargs["messages"][0]["content"]
        assert "San Jose" in user_content
        assert "68" in user_content
        assert "clear sky" in user_content

    @pytest.mark.asyncio()
    async def test_generate_forecast_api_error(self) -> None:
        """Test that API errors are re-raised."""
        import anthropic

        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = anthropic.APIConnectionError(
            request=MagicMock(),
        )

        with patch(
            "weather_friend.services.message_service.anthropic.AsyncAnthropic",
            return_value=mock_client,
        ):
            service = MessageService(api_key="fake-key")
            service.client = mock_client

            with pytest.raises(anthropic.APIError):
                await service.generate_forecast_message(_sample_weather())

    @pytest.mark.asyncio()
    async def test_generate_forecast_empty_response(self) -> None:
        """Test that an empty response raises ValueError."""
        mock_response = MagicMock()
        mock_response.content = []

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        with patch(
            "weather_friend.services.message_service.anthropic.AsyncAnthropic",
            return_value=mock_client,
        ):
            service = MessageService(api_key="fake-key")
            service.client = mock_client

            with pytest.raises(ValueError, match="empty response"):
                await service.generate_forecast_message(_sample_weather())

    def test_system_prompt_contains_personality(self) -> None:
        """Test that the system prompt defines the Oracle personality."""
        assert "Oracle of the Skies" in ORACLE_SYSTEM_PROMPT
        assert "clothing" in ORACLE_SYSTEM_PROMPT
        assert "ALL genders" in ORACLE_SYSTEM_PROMPT

    def test_user_prompt_template_has_placeholders(self) -> None:
        """Test that the user prompt template has all required placeholders."""
        assert "{city}" in USER_PROMPT_TEMPLATE
        assert "{temp_f" in USER_PROMPT_TEMPLATE
        assert "{humidity}" in USER_PROMPT_TEMPLATE
        assert "{wind_speed_mph" in USER_PROMPT_TEMPLATE

    def test_model_constant_is_defined(self) -> None:
        """Test that the Claude model ID is a module-level constant."""
        assert CLAUDE_MODEL
        assert "claude" in CLAUDE_MODEL
