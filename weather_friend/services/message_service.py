"""Generates weather forecast messages with outfit advice via Claude API."""

import logging

import anthropic

from weather_friend.models.weather import WeatherData

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

ORACLE_SYSTEM_PROMPT = (
    "You are the Oracle of the Skies \u2014 a friendly weather guide with a touch "
    "of mystical charm who posts daily forecasts in a Discord server.\n\n"
    "Your personality:\n"
    "- Warm and approachable with a light mystical flair\n"
    "- Occasional celestial or elemental nods (the stars suggest, "
    "the winds carry, etc.) but don't overdo it\n"
    "- Include one relevant emoji per sentence (no more)\n\n"
    "Your PRIMARY purpose is practical clothing advice:\n"
    "- List specific clothing suggestions suitable for ALL genders\n"
    "- Cover layers, footwear, and accessories as the weather warrants\n"
    "- Be concrete: name actual items (light jacket, sunglasses, umbrella, "
    "breathable t-shirt, sneakers, etc.)\n"
    "- Adapt suggestions to the temperature range and conditions\n\n"
    "Message format (keep it to 4-6 sentences total):\n"
    "1. A brief weather summary with a hint of Oracle personality\n"
    "2. Clear clothing recommendations (the main event)\n"
    "3. A short, warm sign-off (a small blessing or encouraging word)\n\n"
    "Strike a balance: be helpful first, charming second. "
    "Think friendly neighborhood fortune teller, not Shakespeare."
)

USER_PROMPT_TEMPLATE = (
    "Here is today's weather for {city}:\n\n"
    "- Temperature: {temp_f:.0f}\u00b0F (feels like {feels_like_f:.0f}\u00b0F)\n"
    "- Conditions: {description}\n"
    "- High/Low: {high_f:.0f}\u00b0F / {low_f:.0f}\u00b0F\n"
    "- Humidity: {humidity}%\n"
    "- Wind: {wind_speed_mph:.0f} mph\n\n"
    "Generate a morning weather forecast with practical clothing suggestions."
)


class MessageService:
    """Service for generating weather forecast messages using Claude API.

    Attributes:
        client: Async Anthropic client instance.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the message service.

        Args:
            api_key: Anthropic API key for Claude access.
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate_forecast_message(self, weather: WeatherData) -> str:
        """Generate a forecast message with outfit advice from weather data.

        Args:
            weather: Current weather data to transform into a message.

        Returns:
            A formatted forecast string with clothing suggestions.

        Raises:
            anthropic.APIError: If the Claude API request fails.
            ValueError: If Claude returns an empty response.
        """
        user_prompt = USER_PROMPT_TEMPLATE.format(
            city=weather.city,
            temp_f=weather.temp_f,
            feels_like_f=weather.feels_like_f,
            description=weather.description,
            high_f=weather.high_f,
            low_f=weather.low_f,
            humidity=weather.humidity,
            wind_speed_mph=weather.wind_speed_mph,
        )

        try:
            response = await self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=300,
                system=ORACLE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError:
            logger.exception("Claude API request failed")
            raise

        if not response.content:
            msg = "Claude returned an empty response"
            raise ValueError(msg)

        return response.content[0].text  # type: ignore[union-attr]
