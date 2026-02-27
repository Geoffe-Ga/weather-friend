"""Weather cog: slash command and scheduled morning post."""

import datetime
import logging
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks

from weather_friend.config import Settings
from weather_friend.models.weather import WeatherData
from weather_friend.services.message_service import MessageService
from weather_friend.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


class WeatherCog(commands.Cog):
    """Discord cog providing weather forecasts via command and scheduler.

    Provides a ``/weather`` slash command for on-demand forecasts and
    a scheduled morning post that fires daily at a configured time.

    Attributes:
        bot: The Discord bot instance.
        settings: Application configuration.
        weather_service: Service for fetching weather data.
        message_service: Service for generating forecast messages.
    """

    def __init__(
        self,
        bot: commands.Bot,
        settings: Settings,
        weather_service: WeatherService,
        message_service: MessageService,
    ) -> None:
        """Initialize the weather cog with injected dependencies.

        Args:
            bot: The Discord bot instance.
            settings: Application configuration.
            weather_service: Service for fetching weather data.
            message_service: Service for generating forecast messages.
        """
        self.bot = bot
        self.settings = settings
        self.weather_service = weather_service
        self.message_service = message_service

    async def cog_load(self) -> None:
        """Start the morning forecast loop when the cog loads."""
        schedule_time = self._get_schedule_time()
        self.morning_forecast.change_interval(time=schedule_time)
        self.morning_forecast.start()

    async def cog_unload(self) -> None:
        """Cancel the morning forecast loop when the cog unloads."""
        self.morning_forecast.cancel()

    @app_commands.command(
        name="weather",
        description="Consult the Oracle for today's weather wisdom",
    )
    async def weather_command(self, interaction: discord.Interaction) -> None:
        """Handle the /weather slash command.

        Args:
            interaction: The Discord interaction from the user.
        """
        await interaction.response.defer()
        weather = await self.weather_service.get_current_weather()
        message = await self.message_service.generate_forecast_message(
            weather,
        )
        embed = _build_embed(message, weather)
        await interaction.followup.send(embed=embed)

    @weather_command.error
    async def weather_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        """Handle errors from the /weather command.

        Args:
            interaction: The Discord interaction that triggered the error.
            error: The error that occurred.
        """
        logger.exception("Weather command error: %s", error)
        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "\U0001f32b\ufe0f The Oracle's vision is clouded. "
                    "Try again shortly."
                )
            else:
                await interaction.response.send_message(
                    "\U0001f32b\ufe0f The Oracle's vision is clouded. "
                    "Try again shortly.",
                    ephemeral=True,
                )
        except discord.DiscordException:
            logger.exception("Failed to send error response")

    @tasks.loop(hours=24)
    async def morning_forecast(self) -> None:
        """Post the daily morning forecast to the configured channel."""
        channel = self.bot.get_channel(self.settings.discord_channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            logger.warning(
                "Channel %s not found or not messageable",
                self.settings.discord_channel_id,
            )
            return
        weather = await self.weather_service.get_current_weather()
        message = await self.message_service.generate_forecast_message(
            weather,
        )
        embed = _build_embed(message, weather)
        await channel.send(embed=embed)

    @morning_forecast.before_loop
    async def before_morning_forecast(self) -> None:
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

    @morning_forecast.error
    async def on_morning_forecast_error(self, error: BaseException) -> None:
        """Log loop errors so the loop can retry next interval.

        Args:
            error: The exception that occurred during the loop.
        """
        logger.exception(
            "Morning forecast loop error; will retry next interval: %s",
            error,
        )

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Log errors from cog commands without crashing.

        Args:
            ctx: The command context.
            error: The exception that occurred.
        """
        logger.exception("Cog command error: %s", error)

    def _get_schedule_time(self) -> datetime.time:
        """Build the daily schedule time from settings.

        Returns:
            A time object with Pacific timezone for the morning post.
        """
        return datetime.time(
            hour=self.settings.morning_hour,
            minute=self.settings.morning_minute,
            tzinfo=PACIFIC_TZ,
        )


def _build_embed(message: str, weather: WeatherData) -> discord.Embed:
    """Build a rich Discord embed from a forecast message and weather data.

    Args:
        message: The forecast message text.
        weather: The weather data for field values.

    Returns:
        A Discord Embed with the forecast and weather details.
    """
    icon_url = f"https://openweathermap.org/img/wn/{weather.icon}@2x.png"

    embed = discord.Embed(
        title="\U0001f52e The Oracle Speaks",
        description=message,
        color=discord.Color.purple(),
    )
    embed.set_thumbnail(url=icon_url)
    embed.add_field(
        name="\U0001f321\ufe0f Temperature",
        value=weather.temp_range_summary,
        inline=True,
    )
    embed.add_field(
        name="\U0001f4a7 Humidity",
        value=f"{weather.humidity}%",
        inline=True,
    )
    embed.add_field(
        name="\U0001f4a8 Wind",
        value=f"{weather.wind_speed_mph:.0f} mph",
        inline=True,
    )
    embed.set_footer(
        text=(f"Weather for {weather.city}" " \u2022 Blessed be your day \u2728")
    )

    return embed
