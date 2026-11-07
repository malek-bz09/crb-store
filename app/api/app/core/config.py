"""App settings, read from environment variables or the app/api/.env file.

Every setting can be overridden by an environment variable with the same name in
capitals, e.g. DATABASE_URL=... uv run uvicorn app.main:app
"""

from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    # "development" shows nothing extra today, but lets later code behave differently in production
    environment: str = "development"

    # postgresql+psycopg:// tells SQLAlchemy to talk to PostgreSQL through the psycopg driver
    database_url: str = "postgresql+psycopg://shop:shop@localhost:5432/shop"

    # Websites allowed to call the API from a browser, comma-separated in .env
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # Signs the login tokens. Anyone who knows it can forge an admin login, so it has
    # no default: the app refuses to start without one. SecretStr keeps it out of logs.
    jwt_secret_key: SecretStr = Field(min_length=32)
    access_token_minutes: int = 8 * 60

    # Requests allowed per client IP address, per minute
    login_rate_limit: int = 5
    order_rate_limit: int = 10

    # Placing an order reserves its stock before anyone has confirmed it by phone, so
    # these stop fake orders from emptying the shop: at most this many items in one
    # order, and this many unconfirmed (pending) orders per phone number
    max_units_per_order: int = 20
    max_pending_orders_per_phone: int = 3

    # Where uploaded product photos are saved
    upload_dir: Path = BACKEND_DIR / "data" / "uploads"

    # Flat home-delivery fee in DZD. Keep in sync with DELIVERY_FEE in app/web/src/services/orders.js
    delivery_fee: Decimal = Decimal(600)

    # Times are stored in UTC; "orders per day" and date filters use the shop's local days
    shop_timezone: str = "Africa/Algiers"

    # Match data for the CRB page comes from TheSportsDB (https://www.thesportsdb.com).
    # "123" is its free public key: it's limited to about 30 requests a minute and
    # shows only the top 5 of the league table. A paid key lifts both limits.
    sportsdb_api_key: SecretStr = SecretStr("123")
    sportsdb_api_url: str = "https://www.thesportsdb.com/api/v1/json"
    # TheSportsDB's ids for CR Belouizdad and the Algerian Ligue 1
    crb_team_id: int = 139278
    crb_league_id: int = 4753
    # The season to show, named after the year it starts (2026 = 2026/27).
    # When not set: the current one, switching over in July.
    football_season: int | None = None
    # Keeps the saved match data up to date in the background while the API runs.
    # The tests turn it off.
    football_refresh: bool = True

    @field_validator("football_season", mode="before")
    @classmethod
    def empty_means_unset(cls, value):
        # FOOTBALL_SEASON= (left empty in .env) means "not set"
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Reads the settings once and reuses them afterwards."""
    return Settings()
