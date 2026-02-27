"""Tests for weather_friend.main module."""

from unittest.mock import AsyncMock, patch

import pytest
from discord.ext import commands

from weather_friend.config import Settings
from weather_friend.main import setup_bot


def _mock_settings() -> Settings:
    """Create mock settings for testing."""
    return Settings(
        discord_token="fake-token",
        discord_channel_id=123456789,
        openweather_api_key="fake-weather-key",
        anthropic_api_key="fake-anthropic-key",
    )


class TestSetupBot:
    """Tests for the setup_bot function."""

    @pytest.mark.asyncio()
    async def test_setup_bot_returns_bot(self) -> None:
        """Test that setup_bot returns a configured Bot instance."""
        with (
            patch("weather_friend.main.MessageService"),
            patch(
                "weather_friend.cogs.weather.WeatherCog.cog_load",
                new_callable=AsyncMock,
            ),
        ):
            bot = await setup_bot(_mock_settings())

        assert isinstance(bot, commands.Bot)

    @pytest.mark.asyncio()
    async def test_setup_bot_adds_weather_cog(self) -> None:
        """Test that setup_bot adds the WeatherCog to the bot."""
        with (
            patch("weather_friend.main.MessageService"),
            patch(
                "weather_friend.cogs.weather.WeatherCog.cog_load",
                new_callable=AsyncMock,
            ),
        ):
            bot = await setup_bot(_mock_settings())

        cog = bot.cogs.get("WeatherCog")
        assert cog is not None

    @pytest.mark.asyncio()
    async def test_setup_bot_uses_default_intents(self) -> None:
        """Test that setup_bot uses default intents without privileged ones."""
        with (
            patch("weather_friend.main.MessageService"),
            patch(
                "weather_friend.cogs.weather.WeatherCog.cog_load",
                new_callable=AsyncMock,
            ),
        ):
            bot = await setup_bot(_mock_settings())

        assert bot.intents.guilds is True
        assert bot.intents.message_content is False
