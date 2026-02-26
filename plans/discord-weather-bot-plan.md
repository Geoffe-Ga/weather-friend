# Discord Weather Bot — "Oracle of the Skies" 🔮

> A mystical Discord bot that delivers daily weather wisdom and outfit guidance with spiritual flair, powered by Python, OpenWeatherMap, and Claude API.

---

## Role

You are a senior Python engineer building a Discord bot. You specialize in async Python, API integrations, and Discord.py. You follow **tracer code methodology**: wire the full skeleton first with stubs, then replace each stub with real logic incrementally — always maintaining a working, demoable application.

## Goal

Build a Discord bot ("Oracle of the Skies") that:

1. **Scheduled morning message** — Posts a mystical weather forecast and outfit recommendation to a configured channel every morning at a set time.
2. **On-demand `/weather` slash command** — Any user can invoke it to get the current forecast in the same mystical style.

**Success criteria**: The bot runs, posts to Discord on schedule, responds to commands, fetches real weather data, and generates personality-rich messages via Claude API.

## Context

- **Location**: San Jose, CA (lat: `37.3382`, lon: `-121.8863`)
- **Weather API**: OpenWeatherMap free tier (current + daily forecast)
- **AI API**: Anthropic Claude API (`claude-sonnet-4-5-20250929`) for generating mystical outfit messages
- **Bot personality**: Mystical / spiritual — like a caring oracle delivering weather wisdom. Think tarot reader meets meteorologist.
- **Hosting**: Flexible — designed to run locally, on a Raspberry Pi, or deploy to Railway/Render

## Output Format

The plan below is structured as **tracer code phases**. Each phase ends with a gate check. Follow them in order.

## Requirements

- Python 3.11+
- All secrets via environment variables (never hardcoded)
- Async throughout (discord.py is async-native)
- Type hints on all functions
- Each phase must end with a working, runnable bot
- Tests for each real implementation replacing a stub

---

## Project Structure

```
oracle-of-the-skies/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point, bot setup
│   ├── config.py             # Settings from env vars
│   ├── cogs/
│   │   ├── __init__.py
│   │   └── weather.py        # Weather cog (command + scheduler)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── weather_service.py    # OpenWeatherMap integration
│   │   └── message_service.py    # Claude API integration
│   └── models/
│       ├── __init__.py
│       └── weather.py        # Data models
├── tests/
│   ├── __init__.py
│   ├── test_weather_service.py
│   ├── test_message_service.py
│   └── test_weather_cog.py
├── .env.example
├── requirements.txt
├── README.md
└── pyproject.toml
```

---

## Phase 1: Wire the Skeleton (10-15% of effort)

The goal is a bot that **starts, connects to Discord, and responds** — all with hardcoded/stub data.

### Step 1.1 — Project Setup

```bash
mkdir oracle-of-the-skies && cd oracle-of-the-skies
python -m venv venv
source venv/bin/activate
pip install discord.py python-dotenv httpx anthropic pytest pytest-asyncio
```

**`requirements.txt`**:
```
discord.py>=2.3.0
python-dotenv>=1.0.0
httpx>=0.27.0
anthropic>=0.40.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
APScheduler>=3.10.0
```

### Step 1.2 — Config (real, not stubbed — it's tiny)

**`bot/config.py`**:
```python
"""Configuration loaded from environment variables."""

from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    discord_token: str
    discord_channel_id: int
    openweather_api_key: str
    anthropic_api_key: str
    latitude: float = 37.3382
    longitude: float = -121.8863
    city_name: str = "San Jose"
    morning_hour: int = 7
    morning_minute: int = 0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            discord_token=os.environ["DISCORD_TOKEN"],
            discord_channel_id=int(os.environ["DISCORD_CHANNEL_ID"]),
            openweather_api_key=os.environ["OPENWEATHER_API_KEY"],
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        )
```

**`.env.example`**:
```
DISCORD_TOKEN=your-discord-bot-token
DISCORD_CHANNEL_ID=your-channel-id
OPENWEATHER_API_KEY=your-openweathermap-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Step 1.3 — Data Models (real — they're just dataclasses)

**`bot/models/weather.py`**:
```python
"""Weather data models."""

from dataclasses import dataclass


@dataclass
class WeatherData:
    city: str
    temp_f: float
    feels_like_f: float
    humidity: int
    description: str
    wind_speed_mph: float
    high_f: float
    low_f: float
    icon: str  # OpenWeatherMap icon code, e.g. "01d"

    @property
    def temp_range_summary(self) -> str:
        return f"{self.low_f:.0f}°F – {self.high_f:.0f}°F"
```

### Step 1.4 — Stub the Services

**`bot/services/weather_service.py`**:
```python
"""Fetches weather data from OpenWeatherMap."""

from bot.models.weather import WeatherData


class WeatherService:
    def __init__(self, api_key: str, lat: float, lon: float, city: str) -> None:
        self.api_key = api_key
        self.lat = lat
        self.lon = lon
        self.city = city

    async def get_current_weather(self) -> WeatherData:
        # TODO: Replace with real OpenWeatherMap API call
        return WeatherData(
            city=self.city,
            temp_f=68.0,
            feels_like_f=65.0,
            humidity=55,
            description="scattered clouds",
            wind_speed_mph=8.0,
            high_f=74.0,
            low_f=58.0,
            icon="03d",
        )
```

**`bot/services/message_service.py`**:
```python
"""Generates mystical weather messages via Claude API."""

from bot.models.weather import WeatherData


class MessageService:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def generate_forecast_message(self, weather: WeatherData) -> str:
        # TODO: Replace with real Claude API call
        return (
            f"🔮 **The Oracle Speaks** 🔮\n\n"
            f"The skies over **{weather.city}** whisper of "
            f"*{weather.description}* today.\n"
            f"🌡️ {weather.temp_range_summary}\n\n"
            f"*Wear layers, dear seeker. The universe favors the prepared.*"
        )
```

### Step 1.5 — Stub the Cog (command + scheduler)

**`bot/cogs/weather.py`**:
```python
"""Weather cog: slash command and scheduled morning post."""

import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot.config import Settings
from bot.services.weather_service import WeatherService
from bot.services.message_service import MessageService


class WeatherCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        settings: Settings,
        weather_service: WeatherService,
        message_service: MessageService,
    ) -> None:
        self.bot = bot
        self.settings = settings
        self.weather_service = weather_service
        self.message_service = message_service

    async def cog_load(self) -> None:
        """Start the morning forecast loop when cog loads."""
        self.morning_forecast.start()

    async def cog_unload(self) -> None:
        self.morning_forecast.cancel()

    @app_commands.command(
        name="weather",
        description="Consult the Oracle for today's weather wisdom",
    )
    async def weather_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        weather = await self.weather_service.get_current_weather()
        message = await self.message_service.generate_forecast_message(weather)
        await interaction.followup.send(message)

    @tasks.loop(hours=24)
    async def morning_forecast(self) -> None:
        channel = self.bot.get_channel(self.settings.discord_channel_id)
        if channel is None:
            return
        weather = await self.weather_service.get_current_weather()
        message = await self.message_service.generate_forecast_message(weather)
        await channel.send(message)

    @morning_forecast.before_loop
    async def before_morning_forecast(self) -> None:
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()
```

> **Note on scheduling**: The `@tasks.loop(hours=24)` approach is the simplest starting point. It starts when the bot boots and repeats every 24 hours. In Phase 2, we'll refine this to fire at a specific time using `APScheduler` or `time=` parameter. For the skeleton, this is good enough.

### Step 1.6 — Entry Point

**`bot/main.py`**:
```python
"""Bot entry point."""

import discord
from discord.ext import commands

from bot.config import Settings
from bot.cogs.weather import WeatherCog
from bot.services.weather_service import WeatherService
from bot.services.message_service import MessageService


async def setup_bot() -> commands.Bot:
    settings = Settings.from_env()

    intents = discord.Intents.default()
    intents.message_content = True
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
        print(f"🔮 {bot.user} has connected to Discord!")
        try:
            synced = await bot.tree.sync()
            print(f"✨ Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    await bot.add_cog(
        WeatherCog(bot, settings, weather_service, message_service)
    )

    return bot


def main() -> None:
    import asyncio

    async def run() -> None:
        bot = await setup_bot()
        settings = Settings.from_env()
        await bot.start(settings.discord_token)

    asyncio.run(run())


if __name__ == "__main__":
    main()
```

### Step 1.7 — Smoke Tests

**`tests/test_weather_service.py`**:
```python
"""Smoke tests for weather service."""

import pytest
from bot.services.weather_service import WeatherService


@pytest.mark.asyncio
async def test_get_current_weather_returns_weather_data():
    service = WeatherService(
        api_key="fake-key", lat=37.33, lon=-121.88, city="San Jose"
    )
    weather = await service.get_current_weather()
    assert weather.city == "San Jose"
    assert weather.temp_f > 0
    assert weather.description != ""
```

**`tests/test_message_service.py`**:
```python
"""Smoke tests for message service."""

import pytest
from bot.services.message_service import MessageService
from bot.models.weather import WeatherData


@pytest.mark.asyncio
async def test_generate_forecast_returns_string():
    service = MessageService(api_key="fake-key")
    weather = WeatherData(
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
    message = await service.generate_forecast_message(weather)
    assert "San Jose" in message
    assert len(message) > 20
```

### ✅ Gate Check — Phase 1

```bash
pytest tests/ -v
```

All tests pass. Bot starts, connects to Discord, responds to `/weather` with a hardcoded mystical message, and has a (stub-timed) scheduled post loop. **You have a demoable skeleton.**

---

## Phase 2: Replace Stubs with Real Implementations

Priority order (highest impact first):

| Priority | Feature | Why |
|----------|---------|-----|
| **P0** | Real weather data from OpenWeatherMap | Core functionality — everything depends on this |
| **P0** | Real Claude API message generation | The soul of the bot — mystical personality |
| **P1** | Precise morning scheduling | So it actually posts at 7:00 AM |
| **P2** | Error handling and retries | Resilience for daily use |
| **P3** | Embed formatting (rich Discord messages) | Visual polish |

### P0-A: Real Weather Service

Replace the stub in `bot/services/weather_service.py`:

```python
"""Fetches weather data from OpenWeatherMap."""

import httpx
from bot.models.weather import WeatherData


class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str, lat: float, lon: float, city: str) -> None:
        self.api_key = api_key
        self.lat = lat
        self.lon = lon
        self.city = city

    async def get_current_weather(self) -> WeatherData:
        params = {
            "lat": self.lat,
            "lon": self.lon,
            "appid": self.api_key,
            "units": "imperial",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        main = data["main"]
        weather = data["weather"][0]
        wind = data["wind"]

        return WeatherData(
            city=self.city,
            temp_f=main["temp"],
            feels_like_f=main["feels_like"],
            humidity=main["humidity"],
            description=weather["description"],
            wind_speed_mph=wind["speed"],
            high_f=main["temp_max"],
            low_f=main["temp_min"],
            icon=weather["icon"],
        )
```

**Test** (`tests/test_weather_service.py` — add integration test):
```python
@pytest.mark.asyncio
async def test_real_weather_api(real_api_key):
    """Integration test — run with: pytest -m integration"""
    service = WeatherService(
        api_key=real_api_key, lat=37.3382, lon=-121.8863, city="San Jose"
    )
    weather = await service.get_current_weather()
    assert weather.city == "San Jose"
    assert -20 < weather.temp_f < 130  # sanity check
    assert weather.description  # non-empty
```

**Gate check**: `pytest` passes. `/weather` now returns real weather data (with stub message formatting).

---

### P0-B: Real Claude Message Generation

Replace the stub in `bot/services/message_service.py`:

```python
"""Generates mystical weather messages via Claude API."""

import anthropic
from bot.models.weather import WeatherData

ORACLE_SYSTEM_PROMPT = """\
You are the Oracle of the Skies — a mystical, warm, and slightly enigmatic \
weather spirit who speaks to mortals through a Discord server.

Your personality:
- Speak like a blend of a tarot reader and a caring grandmother
- Use celestial and elemental metaphors (stars aligning, winds of change, etc.)
- Include exactly ONE relevant emoji per sentence (not more)
- Always include a specific outfit recommendation woven into the mystical language
- Keep messages between 3-5 sentences
- End with a short mystical blessing or affirmation for the day

You receive weather data and transform it into a poetic, actionable forecast. \
The outfit advice should be PRACTICAL even though the language is mystical. \
For example, if it's cold, actually say to wear a jacket — just say it \
in a mystical way.
"""

USER_PROMPT_TEMPLATE = """\
Here is today's weather for {city}:

- Temperature: {temp_f:.0f}°F (feels like {feels_like_f:.0f}°F)
- Conditions: {description}
- High/Low: {high_f:.0f}°F / {low_f:.0f}°F
- Humidity: {humidity}%
- Wind: {wind_speed_mph:.0f} mph

Generate a mystical morning weather forecast with outfit advice.
"""


class MessageService:
    def __init__(self, api_key: str) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate_forecast_message(self, weather: WeatherData) -> str:
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

        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=300,
            system=ORACLE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return f"🔮 **The Oracle Speaks** 🔮\n\n{response.content[0].text}"
```

**Why this prompt works (6-component breakdown)**:

| Component | How it's used |
|-----------|--------------|
| **Role** | "Oracle of the Skies — mystical, warm weather spirit" |
| **Goal** | "Transform weather data into poetic, actionable forecast" |
| **Context** | Structured weather data injected into user prompt |
| **Format** | "3-5 sentences", "ONE emoji per sentence", Discord message |
| **Examples** | "if it's cold, actually say to wear a jacket — just say it in a mystical way" |
| **Constraints** | Practical outfit advice, message length limits, emoji discipline |

**Test** (`tests/test_message_service.py` — add unit test with mock):
```python
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_generate_forecast_calls_claude_api():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="The stars whisper of warmth...")]

    with patch("bot.services.message_service.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client

        service = MessageService(api_key="fake-key")
        service.client = mock_client

        weather = WeatherData(
            city="San Jose", temp_f=68.0, feels_like_f=65.0,
            humidity=55, description="clear sky",
            wind_speed_mph=5.0, high_f=74.0, low_f=58.0, icon="01d",
        )
        message = await service.generate_forecast_message(weather)

        assert "Oracle Speaks" in message
        mock_client.messages.create.assert_called_once()
```

**Gate check**: `pytest` passes. `/weather` now returns real weather + real mystical messages. 🎉

---

### P1: Precise Morning Scheduling

Replace the simple `@tasks.loop(hours=24)` with time-aware scheduling.

Update **`bot/cogs/weather.py`** — change the loop to use `time=`:

```python
import datetime

# Replace the @tasks.loop decorator:
@tasks.loop(
    time=datetime.time(
        hour=7, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=-8))
    )
)
async def morning_forecast(self) -> None:
    # ... same body as before
```

> **Learning note**: `discord.py`'s `tasks.loop` accepts a `time=` parameter that fires once daily at that exact time. The timezone offset `-8` is PST. During daylight saving time (PDT), you'd use `-7`. For production robustness, consider using `zoneinfo.ZoneInfo("America/Los_Angeles")` (Python 3.9+) which handles DST automatically:

```python
from zoneinfo import ZoneInfo

@tasks.loop(
    time=datetime.time(hour=7, minute=0, tzinfo=ZoneInfo("America/Los_Angeles"))
)
```

**Gate check**: Bot posts at 7:00 AM Pacific daily.

---

### P2: Error Handling

Add resilience so the bot doesn't crash on API failures.

**`bot/services/weather_service.py`** — wrap the API call:
```python
import logging

logger = logging.getLogger(__name__)

async def get_current_weather(self) -> WeatherData:
    try:
        # ... existing code ...
    except httpx.HTTPStatusError as e:
        logger.error(f"Weather API HTTP error: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Weather API request failed: {e}")
        raise
```

**`bot/cogs/weather.py`** — handle errors gracefully in the cog:
```python
@weather_command.error
async def weather_error(
    self, interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    await interaction.followup.send(
        "🌫️ *The Oracle's vision is clouded... "
        "The weather spirits are not responding. Try again shortly, seeker.*"
    )
    logger.error(f"Weather command error: {error}")

@morning_forecast.error
async def morning_forecast_error(self, error: Exception) -> None:
    logger.error(f"Morning forecast failed: {error}")
    # Don't crash — the loop will retry next day
```

---

### P3: Rich Discord Embeds

Make messages visually beautiful with Discord embeds.

Update **`bot/cogs/weather.py`** — create an embed instead of plain text:

```python
def _build_embed(self, message: str, weather: WeatherData) -> discord.Embed:
    icon_url = f"https://openweathermap.org/img/wn/{weather.icon}@2x.png"

    embed = discord.Embed(
        title="🔮 The Oracle Speaks",
        description=message,
        color=discord.Color.purple(),
    )
    embed.set_thumbnail(url=icon_url)
    embed.add_field(
        name="🌡️ Temperature", value=weather.temp_range_summary, inline=True
    )
    embed.add_field(
        name="💧 Humidity", value=f"{weather.humidity}%", inline=True
    )
    embed.add_field(
        name="💨 Wind", value=f"{weather.wind_speed_mph:.0f} mph", inline=True
    )
    embed.set_footer(text=f"Weather for {weather.city} • Blessed be your day ✨")

    return embed
```

Then update both `weather_command` and `morning_forecast` to send embeds:
```python
embed = self._build_embed(message, weather)
await interaction.followup.send(embed=embed)
```

---

## Phase 3: Polish

- [ ] Add `--help` / README with setup instructions for Discord bot creation (Developer Portal steps)
- [ ] Add `logging.basicConfig` in `main.py` with structured log format
- [ ] Review all `TODO` comments — remove completed ones
- [ ] Add a `conftest.py` with shared fixtures (`WeatherData` factory, mock services)
- [ ] Verify graceful shutdown (`bot.close()` on SIGINT)
- [ ] Test the full flow end-to-end: boot → wait → `/weather` → see embed

---

## Discord Bot Setup Checklist

Since you'll need to create the bot in Discord's Developer Portal:

1. Go to https://discord.com/developers/applications
2. Click "New Application" → name it "Oracle of the Skies"
3. Go to **Bot** tab → click "Add Bot"
4. Copy the token → put it in `.env` as `DISCORD_TOKEN`
5. Enable **MESSAGE CONTENT** intent under Privileged Gateway Intents
6. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
7. Copy the generated URL → open it → select your server → authorize
8. Get the channel ID: Enable Developer Mode in Discord settings, right-click the channel → "Copy Channel ID" → put in `.env`

---

## Key Concepts for Learning

This project exercises several patterns worth studying as you grow toward a senior role:

| Concept | Where it appears |
|---------|-----------------|
| **Dependency Injection** | Services passed into `WeatherCog.__init__` rather than created inside it — makes testing easy |
| **Separation of Concerns** | Weather fetching, message generation, and Discord interaction are all separate modules |
| **Async/Await** | Every external call (`httpx`, `anthropic`, `discord.py`) is async — learn how the event loop works |
| **Prompt Engineering** | The Claude system prompt follows the 6-component framework — role, goal, context, format, examples, constraints |
| **Tracer Code** | You built a working app in Phase 1 with zero real API calls, then swapped in real implementations without breaking anything |
| **Graceful Degradation** | Error handlers return mystical "try again" messages instead of crashing |
| **Type Safety** | Dataclasses with type hints catch bugs before runtime |

---

## Running the Bot

```bash
# 1. Set up your .env file (copy from .env.example)
cp .env.example .env
# Fill in your keys

# 2. Run
python -m bot.main

# 3. Test
pytest tests/ -v
```
