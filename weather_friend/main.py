"""Bot entry point for Oracle of the Skies."""

import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from weather_friend.cogs.weather import WeatherCog
from weather_friend.config import Settings
from weather_friend.services.message_service import MessageService
from weather_friend.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


async def setup_bot(settings: Settings) -> commands.Bot:
    """Create and configure the Discord bot with all cogs.

    Args:
        settings: Application configuration with API keys and settings.

    Returns:
        A configured Bot instance ready to be started.
    """
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)

    weather_service = WeatherService(
        api_key=settings.openweather_api_key,
        lat=settings.latitude,
        lon=settings.longitude,
        city=settings.city_name,
    )
    message_service = MessageService(api_key=settings.anthropic_api_key)

    @bot.event
    async def on_ready() -> None:
        """Log bot connection and sync slash commands."""
        logger.info("Bot %s has connected to Discord!", bot.user)
        synced = await bot.tree.sync()
        logger.info("Synced %d command(s)", len(synced))

    await bot.add_cog(WeatherCog(bot, settings, weather_service, message_service))

    return bot


def main() -> None:
    """Run the Oracle of the Skies Discord bot."""
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = Settings.from_env()

    async def run() -> None:
        """Start the bot with the configured settings."""
        bot = await setup_bot(settings)
        await bot.start(settings.discord_token)

    asyncio.run(run())


if __name__ == "__main__":
    main()
