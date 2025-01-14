from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class SystemSettings(BaseSettings):
    """Settings that apply to the whole system"""

    app_env: str = Field("development", env="APP_ENV")
    timezone: str = Field("UTC", env="TIMEZONE")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    allowed_hosts: List[str] = ["*"]  # For local development. Change in prod
    scheduler_timezone: str = Field("UTC", env="SCHEDULER_TIMEZONE")
    task_store_url: str = Field("sqlite:///tasks.db", env="TASK_STORE_URL")

    class Config:
        env_prefix = ""  # No prefix on env


class PostgresSettings(BaseSettings):
    """Settings for Postgres Connection"""

    pg_host: str = Field("localhost", env="PG_HOST")
    pg_port: int = Field(5432, env="PG_PORT")
    pg_user: str = Field("user", env="PG_USER")
    pg_pass: str = Field("password", env="PG_PASS")
    pg_db: str = Field("swap", env="PG_DB")

    class Config:
        env_prefix = "pg_"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.pg_user}:{self.pg_pass}@{self.pg_host}:{self.pg_port}/{self.pg_db}"


class SQLiteSettings(BaseSettings):
    """Settings if using SQLite"""

    sqlite_file: str = Field("swap.db", env="SQLITE_FILE")

    class Config:
        env_prefix = "sqlite_"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.sqlite_file}"


class GoogleCalendarSettings(BaseSettings):
    """Settings for Google Calendar API integration."""

    gcal_client_id: str = Field(..., env="GCAL_CLIENT_ID")
    gcal_client_secret: str = Field(..., env="GCAL_CLIENT_SECRET")
    gcal_token_uri: str = Field(
        "https://oauth2.googleapis.com/token", env="GCAL_TOKEN_URI"
    )
    gcal_scopes: List[str] = Field(
        [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
        ],
        env="GCAL_SCOPES",
    )

    class Config:
        env_prefix = "gcal_"


class TelegramSettings(BaseSettings):
    """Settings for Telegram bot integration."""

    tg_bot_token: str = Field(..., env="TG_BOT_TOKEN")
    tg_webhook_url: Optional[str] = Field(None, env="TG_WEBHOOK_URL")

    class Config:
        env_prefix = "tg_"


class RotaSettings(BaseSettings):
    """Settings for Rota integration."""

    # spreadsheet_id: str = Field(
    #     "1MqJwH59lHhE6q0kmFNkQZzpteRLTQBlX2vKhEhVltHQ", env="SPREADSHEET_ID"
    # )
    # range_name: str = Field("Combined Rota!A:M", env="RANGE_NAME")
    spreadsheet_id: str = Field(
        "1shLCkqxoZSJKLq2f4yhAG71iCHHJ3tlnr4bV9zAFZ3g", env="SPREADSHEET_ID"
    )
    range_name: str = Field("Sheet1!A:M", env="RANGE_NAME")


class Settings(BaseSettings):
    """Aggregated settings for the entire application."""

    system: SystemSettings = SystemSettings()
    postgres: Optional[PostgresSettings] = None
    sqlite: Optional[SQLiteSettings] = SQLiteSettings()
    rota: RotaSettings = RotaSettings()
    # gcal: GoogleCalendarSettings = GoogleCalendarSettings()
    # telegram: TelegramSettings = TelegramSettings()

    task_store_url = property(lambda self: self.system.task_store_url)

    @property
    def database_url(self):
        if self.postgres:
            return self.postgres.database_url
        elif self.sqlite:
            return self.sqlite.database_url
        return None

    @property
    def scheduler_timezone(self):
        return self.system.scheduler_timezone


settings = Settings()
