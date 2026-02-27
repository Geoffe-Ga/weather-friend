"""Configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables.

    Attributes:
        discord_token: Discord bot authentication token.
        discord_channel_id: Channel ID for scheduled forecast posts.
        openweather_api_key: OpenWeatherMap API key.
        anthropic_api_key: Anthropic Claude API key.
        latitude: Location latitude for weather queries.
        longitude: Location longitude for weather queries.
        city_name: Display name for the forecast city.
        morning_hour: Hour (0-23) for scheduled morning forecast.
        morning_minute: Minute (0-59) for scheduled morning forecast.
    """

    discord_token: str
    discord_channel_id: int
    openweather_api_key: str
    anthropic_api_key: str
    latitude: float = 37.3382
    longitude: float = -121.8863
    city_name: str = "San Jose"
    morning_hour: int = 7
    morning_minute: int = 0

    def __post_init__(self) -> None:
        """Validate field ranges after initialization.

        Raises:
            ValueError: If morning_hour or morning_minute is out of range.
        """
        if not 0 <= self.morning_hour <= 23:
            msg = f"morning_hour must be 0-23, got {self.morning_hour}"
            raise ValueError(msg)
        if not 0 <= self.morning_minute <= 59:
            msg = "morning_minute must be 0-59, " f"got {self.morning_minute}"
            raise ValueError(msg)

    @classmethod
    def from_env(cls) -> "Settings":
        """Create Settings from environment variables.

        Returns:
            A Settings instance populated from the environment.

        Raises:
            KeyError: If a required environment variable is missing.
            ValueError: If DISCORD_CHANNEL_ID is not a valid integer,
                or if morning_hour/morning_minute are out of range.
        """
        return cls(
            discord_token=os.environ["DISCORD_TOKEN"],
            discord_channel_id=int(os.environ["DISCORD_CHANNEL_ID"]),
            openweather_api_key=os.environ["OPENWEATHER_API_KEY"],
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        )
