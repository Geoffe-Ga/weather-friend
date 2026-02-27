"""Tests for weather_friend.cogs.weather module."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from weather_friend.cogs.weather import WeatherCog, _build_embed
from weather_friend.config import Settings
from weather_friend.models.weather import WeatherData
from weather_friend.services.message_service import MessageService
from weather_friend.services.weather_service import WeatherService


def _make_cog(
    channel: object | None = None,
) -> tuple[WeatherCog, AsyncMock, AsyncMock]:
    """Create a WeatherCog with mocked dependencies.

    Args:
        channel: Optional mock channel to return from bot.get_channel.

    Returns:
        Tuple of (cog, mock_weather_service, mock_message_service).
    """
    bot = MagicMock(spec=["get_channel", "wait_until_ready"])
    bot.get_channel.return_value = channel
    bot.wait_until_ready = AsyncMock()

    settings = Settings(
        discord_token="fake-token",
        discord_channel_id=123456789,
        openweather_api_key="fake-weather-key",
        anthropic_api_key="fake-anthropic-key",
    )

    mock_weather_svc = AsyncMock(spec=WeatherService)
    mock_message_svc = AsyncMock(spec=MessageService)

    cog = WeatherCog(
        bot=bot,
        settings=settings,
        weather_service=mock_weather_svc,
        message_service=mock_message_svc,
    )
    return cog, mock_weather_svc, mock_message_svc


def _sample_weather() -> WeatherData:
    """Create a sample WeatherData for testing."""
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


class TestWeatherCog:
    """Tests for the WeatherCog class."""

    def test_init_stores_dependencies(self) -> None:
        """Test that the cog stores all injected dependencies."""
        cog, weather_svc, message_svc = _make_cog()
        assert cog.settings.discord_token == "fake-token"
        assert cog.weather_service is weather_svc
        assert cog.message_service is message_svc

    @pytest.mark.asyncio()
    async def test_weather_command_sends_embed(self) -> None:
        """Test /weather command fetches data and sends an embed."""
        cog, weather_svc, message_svc = _make_cog()
        weather_svc.get_current_weather.return_value = _sample_weather()
        message_svc.generate_forecast_message.return_value = (
            "The stars whisper of clouds."
        )

        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response = AsyncMock()
        interaction.followup = AsyncMock()

        callback = cog.weather_command.callback
        await callback(cog, interaction)  # type: ignore[call-arg,arg-type]

        interaction.response.defer.assert_called_once()
        weather_svc.get_current_weather.assert_called_once()
        message_svc.generate_forecast_message.assert_called_once()
        interaction.followup.send.assert_called_once()

        call_kwargs = interaction.followup.send.call_args.kwargs
        embed = call_kwargs["embed"]
        assert isinstance(embed, discord.Embed)

    @pytest.mark.asyncio()
    async def test_morning_forecast_posts_to_channel(self) -> None:
        """Test scheduled forecast sends embed to the configured channel."""
        mock_channel = AsyncMock(spec=discord.TextChannel)
        cog, weather_svc, message_svc = _make_cog(
            channel=mock_channel,
        )
        weather_svc.get_current_weather.return_value = _sample_weather()
        message_svc.generate_forecast_message.return_value = (
            "Morning wisdom from the Oracle."
        )

        await cog.morning_forecast.coro(cog)

        weather_svc.get_current_weather.assert_called_once()
        message_svc.generate_forecast_message.assert_called_once()
        mock_channel.send.assert_called_once()

        call_kwargs = mock_channel.send.call_args.kwargs
        assert isinstance(call_kwargs["embed"], discord.Embed)

    @pytest.mark.asyncio()
    async def test_morning_forecast_skips_when_channel_missing(
        self,
    ) -> None:
        """Test scheduled forecast does nothing if channel is not found."""
        cog, weather_svc, _message_svc = _make_cog(channel=None)

        await cog.morning_forecast.coro(cog)

        weather_svc.get_current_weather.assert_not_called()

    @pytest.mark.asyncio()
    async def test_morning_forecast_skips_non_messageable_channel(
        self,
    ) -> None:
        """Test forecast skips channel that is not Messageable."""
        mock_channel = MagicMock(spec=discord.CategoryChannel)
        cog, weather_svc, _message_svc = _make_cog(
            channel=mock_channel,
        )

        await cog.morning_forecast.coro(cog)

        weather_svc.get_current_weather.assert_not_called()

    @pytest.mark.asyncio()
    async def test_cog_load_starts_loop_with_schedule_time(
        self,
    ) -> None:
        """Test that cog_load configures and starts the morning loop."""
        cog, _, _ = _make_cog()
        with (
            patch.object(cog.morning_forecast, "change_interval") as mock_change,
            patch.object(cog.morning_forecast, "start") as mock_start,
        ):
            await cog.cog_load()
            mock_change.assert_called_once()
            schedule_time = mock_change.call_args.kwargs["time"]
            assert schedule_time.hour == 7
            assert schedule_time.minute == 0
            mock_start.assert_called_once()

    @pytest.mark.asyncio()
    async def test_cog_unload_cancels_loop(self) -> None:
        """Test that cog_unload cancels the morning forecast loop."""
        cog, _, _ = _make_cog()
        with patch.object(cog.morning_forecast, "cancel") as mock_cancel:
            await cog.cog_unload()
            mock_cancel.assert_called_once()

    def test_get_schedule_time_uses_settings(self) -> None:
        """Test _get_schedule_time uses hour/minute from settings."""
        cog, _, _ = _make_cog()
        schedule_time = cog._get_schedule_time()
        assert schedule_time.hour == 7
        assert schedule_time.minute == 0
        assert schedule_time.tzinfo is not None

    @pytest.mark.asyncio()
    async def test_weather_error_after_defer(self) -> None:
        """Test error handler sends followup when defer succeeded."""
        cog, _, _ = _make_cog()
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = True
        interaction.followup = AsyncMock()

        from discord import app_commands

        error = app_commands.AppCommandError("test error")
        await cog.weather_error(interaction, error)

        interaction.followup.send.assert_called_once()

    @pytest.mark.asyncio()
    async def test_weather_error_before_defer(self) -> None:
        """Test error handler sends initial response when defer failed."""
        cog, _, _ = _make_cog()
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.send_message = AsyncMock()

        from discord import app_commands

        error = app_commands.AppCommandError("test error")
        await cog.weather_error(interaction, error)

        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio()
    async def test_morning_forecast_error_handler_logs(self) -> None:
        """Test that the loop error handler logs and does not re-raise."""
        cog, _, _ = _make_cog()
        error = RuntimeError("transient network error")

        # Should not raise — just log
        await cog.on_morning_forecast_error(error)


class TestBuildEmbed:
    """Tests for the _build_embed helper function."""

    def test_embed_title(self) -> None:
        """Test that the embed has the Oracle title."""
        embed = _build_embed("Test message", _sample_weather())
        assert "Oracle Speaks" in (embed.title or "")

    def test_embed_description(self) -> None:
        """Test that the embed description contains the message."""
        embed = _build_embed("Mystical forecast text", _sample_weather())
        assert embed.description == "Mystical forecast text"

    def test_embed_color_is_purple(self) -> None:
        """Test that the embed uses purple color."""
        embed = _build_embed("msg", _sample_weather())
        assert embed.color == discord.Color.purple()

    def test_embed_has_three_fields(self) -> None:
        """Test that the embed has temperature, humidity, and wind fields."""
        embed = _build_embed("msg", _sample_weather())
        assert len(embed.fields) == 3
        field_names = [f.name for f in embed.fields]
        assert any("Temperature" in (n or "") for n in field_names)
        assert any("Humidity" in (n or "") for n in field_names)
        assert any("Wind" in (n or "") for n in field_names)

    def test_embed_temperature_field_value(self) -> None:
        """Test that the temperature field shows the correct range."""
        weather = _sample_weather()
        embed = _build_embed("msg", weather)
        temp_field = next(f for f in embed.fields if "Temperature" in (f.name or ""))
        assert temp_field.value == weather.temp_range_summary

    def test_embed_humidity_field_value(self) -> None:
        """Test that the humidity field shows the correct percentage."""
        embed = _build_embed("msg", _sample_weather())
        humidity_field = next(f for f in embed.fields if "Humidity" in (f.name or ""))
        assert humidity_field.value == "55%"

    def test_embed_wind_field_value(self) -> None:
        """Test that the wind field shows the correct speed."""
        embed = _build_embed("msg", _sample_weather())
        wind_field = next(f for f in embed.fields if "Wind" in (f.name or ""))
        assert wind_field.value == "8 mph"

    def test_embed_footer_contains_city(self) -> None:
        """Test that the footer contains the city name."""
        embed = _build_embed("msg", _sample_weather())
        assert "San Jose" in (embed.footer.text or "")

    def test_embed_thumbnail_uses_weather_icon(self) -> None:
        """Test that the thumbnail URL uses the weather icon code."""
        embed = _build_embed("msg", _sample_weather())
        assert "03d" in (embed.thumbnail.url or "")
