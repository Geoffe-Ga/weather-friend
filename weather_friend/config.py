"""Configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from typing import Final

from weather_friend.auth_middleware import SECRET_ENV_VAR

DEFAULT_LATITUDE: Final[float] = 37.3382
DEFAULT_LONGITUDE: Final[float] = -121.8863
DEFAULT_CITY_NAME: Final[str] = "San Jose"

DEFAULT_API_HOST: Final[str] = "127.0.0.1"
DEFAULT_API_PORT: Final[int] = 8002
API_PORT_ENV_VAR: Final[str] = "WEATHER_FRIEND_API_PORT"


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
    latitude: float = DEFAULT_LATITUDE
    longitude: float = DEFAULT_LONGITUDE
    city_name: str = DEFAULT_CITY_NAME
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
            msg = f"morning_minute must be 0-59, got {self.morning_minute}"
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


@dataclass(frozen=True)
class ApiSettings:
    """Settings for the standalone RubotPaul API process.

    After the RubotPaul cutover the API is the entire service (a
    ``systemd --user`` unit on the VPS bound to localhost), so unlike
    Settings no Discord credentials are required.

    Attributes:
        openweather_api_key: OpenWeatherMap API key.
        anthropic_api_key: Anthropic Claude API key for narratives.
        host: Interface the API binds to (localhost-only on the VPS).
        port: TCP port the API listens on.
        latitude: Location latitude for weather queries.
        longitude: Location longitude for weather queries.
        city_name: Display name for the forecast city.
    """

    openweather_api_key: str
    anthropic_api_key: str
    host: str = DEFAULT_API_HOST
    port: int = DEFAULT_API_PORT
    latitude: float = DEFAULT_LATITUDE
    longitude: float = DEFAULT_LONGITUDE
    city_name: str = DEFAULT_CITY_NAME

    def __post_init__(self) -> None:
        """Validate field ranges after initialization.

        Raises:
            ValueError: If port is outside the valid TCP range.
        """
        if not 1 <= self.port <= 65535:
            msg = f"port must be 1-65535, got {self.port}"
            raise ValueError(msg)

    @classmethod
    def from_env(cls) -> "ApiSettings":
        """Create ApiSettings from environment variables.

        RUBOTPAUL_SHARED_SECRET is validated here (fail fast at boot with
        a clear message) even though the auth middleware reads it from the
        environment on each request.

        Returns:
            An ApiSettings instance populated from the environment.

        Raises:
            RuntimeError: If any required environment variable is unset,
                naming every missing variable.
            ValueError: If WEATHER_FRIEND_API_PORT is not a valid port.
        """
        required = ("OPENWEATHER_API_KEY", "ANTHROPIC_API_KEY", SECRET_ENV_VAR)
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            msg = "missing required environment variables: " + ", ".join(missing)
            raise RuntimeError(msg)
        raw_port = os.environ.get(API_PORT_ENV_VAR, str(DEFAULT_API_PORT))
        try:
            port = int(raw_port)
        except ValueError as exc:
            msg = f"{API_PORT_ENV_VAR} must be an integer, got {raw_port!r}"
            raise ValueError(msg) from exc
        return cls(
            openweather_api_key=os.environ["OPENWEATHER_API_KEY"],
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            port=port,
        )
