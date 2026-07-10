# weather-friend

**Oracle of the Skies** — a Discord bot that protects invisible labor by
remembering the weather, deciding what everyone should wear, and posting it
to your household channel before the day begins.

---

## Mission

Every household has someone who silently runs the weather check. They open
the app, glance at the forecast, mentally translate "47°F with wind" into
"long pants, the heavier jacket, and the rain shell just in case," and then
remind everyone else on the way out the door. That work is real, it is
constant, and it is rarely counted.

**weather-friend exists to make that work disappear into a bot.**

The Oracle posts a daily forecast to a Discord channel each morning with
specific, gender-neutral clothing suggestions — layers, footwear,
accessories — written in plain language anyone can follow. No one has to
remember. No one has to translate. No one has to nag. The mental load that
used to live in one person's head now lives in a scheduled task.

This is a small bot with a focused goal: redistribute a tiny piece of
invisible labor so the people who carry it can carry less.

---

## How It Works

Every morning at 7:00 AM Pacific (configurable), the bot:

1. Pulls current conditions for a configured location from
   **OpenWeatherMap**.
2. Sends those conditions to **Claude** (`claude-sonnet-4-5`) with a system
   prompt that instructs it to reply as the "Oracle of the Skies" — warm,
   lightly mystical, and **primarily focused on practical, inclusive
   clothing advice**.
3. Posts the result as a rich Discord embed with the temperature range,
   humidity, wind, and a weather icon.

A `/weather` slash command runs the same pipeline on demand.

---

## Architecture

The codebase follows a small, layered structure. Each layer depends only on
the one beneath it.

```
┌──────────────────────────────────────────────┐
│  Discord (Cog Layer)                         │
│  weather_friend/cogs/weather.py              │
│   • /weather slash command                   │
│   • daily morning_forecast scheduled task    │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Services (Application Layer)                │
│  weather_friend/services/                    │
│   • WeatherService  → OpenWeatherMap (httpx) │
│   • MessageService  → Claude (anthropic SDK) │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Models (Domain Layer)                       │
│  weather_friend/models/weather.py            │
│   • WeatherData (frozen dataclass)           │
└──────────────────────────────────────────────┘

         Configuration: weather_friend/config.py
         Entry point:   weather_friend/main.py
```

### Module map

| Path | Responsibility |
|------|----------------|
| `weather_friend/main.py` | Bot entry point. Loads `.env`, builds `Settings`, wires services into the cog, and starts the Discord client. |
| `weather_friend/config.py` | `Settings` frozen dataclass. Loads required env vars and validates schedule fields. |
| `weather_friend/cogs/weather.py` | `WeatherCog`: the `/weather` command, the daily `morning_forecast` task, and embed rendering. |
| `weather_friend/services/weather_service.py` | `WeatherService`: async OpenWeatherMap client returning a `WeatherData`. |
| `weather_friend/services/message_service.py` | `MessageService`: builds the Oracle prompt and calls the Anthropic Claude API. |
| `weather_friend/models/weather.py` | `WeatherData` immutable dataclass + `temp_range_summary` formatter. |

---

## Code Choices

A short tour of why the codebase looks the way it does.

- **discord.py with cogs.** A cog is a clean way to bundle a command,
  scheduled task, and error handlers under one object with shared
  dependencies. `WeatherCog` receives its `WeatherService` and
  `MessageService` via constructor injection, which keeps the Discord layer
  testable without spinning up a real bot.
- **Constructor injection over module globals.** Services are constructed
  once in `main.py` and passed down. Nothing reaches into a global client.
  This lets tests substitute fakes and lets the schedule run with the same
  objects the slash command uses.
- **Frozen dataclasses for config and data.** `Settings` and `WeatherData`
  are `@dataclass(frozen=True)`. Configuration can't drift mid-run, and
  weather payloads can't be mutated by accident as they pass through layers.
- **`httpx.AsyncClient` for HTTP.** Async-native, plays nicely with
  `discord.py`'s event loop, supports timeouts (set to 10s), and raises
  typed errors (`HTTPStatusError`, `RequestError`) that the service catches,
  logs, and re-raises so callers see real failure modes.
- **Anthropic async SDK with a system prompt.** The Oracle's voice and the
  "clothing advice is the main event" instruction live in
  `ORACLE_SYSTEM_PROMPT` as a single editable string. The user prompt is a
  template populated from `WeatherData` fields — no string concatenation
  scattered across the code.
- **`discord.ext.tasks` for scheduling.** `@tasks.loop(hours=24)` paired
  with `change_interval(time=...)` runs the morning post at a specific
  Pacific-time wall-clock moment without dragging in a separate scheduler
  dependency. Errors in the loop are logged and the loop continues.
- **`zoneinfo.ZoneInfo("America/Los_Angeles")`.** Stdlib timezones, no
  `pytz`. The schedule respects DST automatically.
- **Imperial units at the API boundary.** OpenWeatherMap is queried with
  `units=imperial` so the Oracle's audience gets °F and mph without an
  extra conversion layer.
- **Strict typing, top to bottom.** `mypy` runs in strict mode
  (`disallow_untyped_defs`, `warn_return_any`, etc.) and ruff is configured
  with a broad rule set. Every public function has Google-style docstrings
  with `Args`, `Returns`, `Raises`.
- **Heroku-friendly deployment.** A `Procfile` runs the bot as a `worker`
  dyno (`python -m weather_friend.main`) and `runtime.txt` pins the Python
  version. No web server, no port binding — just a long-lived process.

---

## API Reference

### Discord interface

| Surface | Trigger | Behavior |
|---------|---------|----------|
| `/weather` | User invokes the slash command in any channel the bot can see. | Defers the response, fetches current weather, generates an Oracle message, replies with a rich embed. |
| Daily morning post | Scheduled task fires at `MORNING_HOUR:MORNING_MINUTE` Pacific time. | Posts the same embed to the channel ID in `DISCORD_CHANNEL_ID`. |

The embed includes:

- **Title:** "🔮 The Oracle Speaks"
- **Description:** Claude-generated forecast + clothing recommendations
- **Thumbnail:** OpenWeatherMap condition icon
- **Fields:** Temperature range (low–high °F), humidity %, wind mph
- **Footer:** "Weather for {city} • Blessed be your day ✨"

### Internal Python API

#### `weather_friend.config.Settings`

Frozen dataclass loaded from environment variables.

```python
Settings.from_env() -> Settings
```

Required env vars: `DISCORD_TOKEN`, `DISCORD_CHANNEL_ID`,
`OPENWEATHER_API_KEY`, `ANTHROPIC_API_KEY`. Optional fields default to San
Jose, CA at 7:00 AM Pacific. Raises `KeyError` for missing required vars,
`ValueError` for an invalid `DISCORD_CHANNEL_ID` or out-of-range schedule.

#### `weather_friend.services.weather_service.WeatherService`

```python
WeatherService(api_key: str, lat: float, lon: float, city: str)

async WeatherService.get_current_weather() -> WeatherData
```

Calls `GET https://api.openweathermap.org/data/2.5/weather` with `lat`,
`lon`, `appid`, and `units=imperial`. 10-second timeout. Raises
`httpx.HTTPStatusError` on non-2xx responses and `httpx.RequestError` on
network failure.

#### `weather_friend.services.message_service.MessageService`

```python
MessageService(api_key: str)

async MessageService.generate_forecast_message(weather: WeatherData) -> str
```

Calls Claude (`claude-sonnet-4-5-20250929`) with a 300-token cap, the
Oracle system prompt, and a templated user message containing the
`WeatherData` fields. Raises `anthropic.APIError` on API failure and
`ValueError` if the response is empty.

#### `weather_friend.models.weather.WeatherData`

Immutable dataclass with `city`, `temp_f`, `feels_like_f`, `humidity`,
`description`, `wind_speed_mph`, `high_f`, `low_f`, `icon`, plus the
`temp_range_summary` property (`"54°F – 68°F"`).

### External APIs used

| API | Purpose | Auth |
|-----|---------|------|
| **OpenWeatherMap** Current Weather Data | Source of truth for conditions. | `appid` query parameter. |
| **Anthropic Messages API** | Generates the Oracle's clothing advice. | `ANTHROPIC_API_KEY` via SDK. |
| **Discord Gateway / Application Commands** | Slash commands and channel posts. | Bot token. |

---

## Configuration

Copy `.env.example` to `.env` and fill in:

```bash
DISCORD_TOKEN=...           # Bot token from the Discord Developer Portal
DISCORD_CHANNEL_ID=...      # Channel ID for the daily post
OPENWEATHER_API_KEY=...     # https://openweathermap.org/api
ANTHROPIC_API_KEY=...       # https://console.anthropic.com/
```

Optional overrides (defaults shown) live in `Settings`: `latitude=37.3382`,
`longitude=-121.8863`, `city_name="San Jose"`, `morning_hour=7`,
`morning_minute=0`. Adjust by editing `config.py` or extending
`Settings.from_env`.

---

## Installation

```bash
git clone <repository-url>
cd weather-friend

pip install -r requirements-dev.txt
pre-commit install
```

## Running

```bash
python -m weather_friend.main
```

Or via the `Procfile` worker entry:

```bash
honcho start worker
```

## Running the standalone RubotPaul API

After the RubotPaul cutover, the HTTP API is the entire service — no
Discord bot process. It binds to `127.0.0.1` on `WEATHER_FRIEND_API_PORT`
(default `8002`) and needs only `OPENWEATHER_API_KEY`, `ANTHROPIC_API_KEY`,
and `RUBOTPAUL_SHARED_SECRET`:

```bash
python -m weather_friend.api
```

RubotPaul calls it locally on the VPS with an HMAC bearer token minted
from the shared secret:

```bash
curl -H "Authorization: Bearer <caller_id>.<timestamp>.<hmac_hex>" \
  "http://127.0.0.1:8002/api/v1/weather/data?location=San+Jose,CA"
curl "http://127.0.0.1:8002/healthz"   # unauthenticated liveness probe
```

Sample `systemd --user` unit (`~/.config/systemd/user/weather-friend.service`;
localhost-only binding, so no Tailscale-IP wiring is needed):

```ini
[Unit]
Description=weather-friend API for RubotPaul
After=network.target

[Service]
WorkingDirectory=%h/weather-friend
EnvironmentFile=%h/weather-friend/.env
ExecStart=%h/weather-friend/.venv/bin/python -m weather_friend.api
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now weather-friend.service
```

---

## Development

### Quality scripts

Always invoke tools through `./scripts/*` instead of running them directly.

```bash
./scripts/check-all.sh     # everything: format, lint, types, tests, security
./scripts/test.sh          # pytest with branch coverage
./scripts/lint.sh          # ruff + mypy
./scripts/format.sh --fix  # black + isort
./scripts/security.sh      # bandit + pip-audit
./scripts/mutation.sh      # mutmut
```

### Quality bar

| Metric | Threshold |
|--------|-----------|
| Branch test coverage | ≥ 90% |
| Mutation score | ≥ 80% |
| Cyclomatic complexity | ≤ 10 per function |
| mypy | strict, no unjustified `# type: ignore` |
| Ruff | clean across `E,W,F,I,N,UP,B,C4,SIM,TCH,RUF` |
| Bandit | no findings |

CI enforces these gates. See `CLAUDE.md` for the full Stay Green workflow.

### Project layout

```
weather-friend/
├── weather_friend/
│   ├── main.py               # Bot entry point
│   ├── config.py             # Settings dataclass
│   ├── cogs/weather.py       # /weather + scheduled morning post
│   ├── services/
│   │   ├── weather_service.py   # OpenWeatherMap client
│   │   └── message_service.py   # Claude client + Oracle prompt
│   └── models/weather.py     # WeatherData
├── tests/                    # Unit + integration tests
├── scripts/                  # Quality control scripts
├── .github/workflows/        # CI / security / dependency review
├── pyproject.toml            # Tool config (mypy strict, coverage 90%)
├── .pre-commit-config.yaml   # 32 quality checks
├── Procfile                  # Heroku worker definition
└── runtime.txt               # Python 3.11.11
```

---

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green) — maximum quality Python projects from day one.
