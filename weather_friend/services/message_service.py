"""Generates mystical weather messages via Claude API."""

import logging

import anthropic

from weather_friend.models.weather import WeatherData

logger = logging.getLogger(__name__)

ORACLE_SYSTEM_PROMPT = (
    "You are the Oracle of the Skies \u2014 a mystical, warm, and slightly enigmatic "
    "weather spirit who speaks to mortals through a Discord server.\n\n"
    "Your personality:\n"
    "- Speak like a blend of a tarot reader and a caring grandmother\n"
    "- Use celestial and elemental metaphors (stars aligning, winds of change, etc.)\n"
    "- Include exactly ONE relevant emoji per sentence (not more)\n"
    "- Always include a specific outfit recommendation "
    "woven into the mystical language\n"
    "- Keep messages between 3-5 sentences\n"
    "- End with a short mystical blessing or affirmation for the day\n\n"
    "You receive weather data and transform it into a poetic, actionable forecast. "
    "The outfit advice should be PRACTICAL even though the language is mystical. "
    "For example, if it's cold, actually say to wear a jacket \u2014 just say it "
    "in a mystical way."
)

USER_PROMPT_TEMPLATE = (
    "Here is today's weather for {city}:\n\n"
    "- Temperature: {temp_f:.0f}\u00b0F (feels like {feels_like_f:.0f}\u00b0F)\n"
    "- Conditions: {description}\n"
    "- High/Low: {high_f:.0f}\u00b0F / {low_f:.0f}\u00b0F\n"
    "- Humidity: {humidity}%\n"
    "- Wind: {wind_speed_mph:.0f} mph\n\n"
    "Generate a mystical morning weather forecast with outfit advice."
)


class MessageService:
    """Service for generating mystical weather messages using Claude API.

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
        """Generate a mystical forecast message from weather data.

        Args:
            weather: Current weather data to transform into a message.

        Returns:
            A formatted mystical forecast string.

        Raises:
            anthropic.APIError: If the Claude API request fails.
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
                model="claude-sonnet-4-5-20250929",
                max_tokens=300,
                system=ORACLE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError:
            logger.exception("Claude API request failed")
            raise

        return response.content[0].text  # type: ignore[union-attr]
