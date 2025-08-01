"""Application settings using pydantic-settings."""

import os
from typing import List, Optional
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class UserConfig(BaseModel):
    """Configuration for a single user."""
    calendar_name: str
    user_name: str
    emails_to_share: List[str]


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite:///swap.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")


class GoogleConfig(BaseModel):
    """Google API configuration."""
    service_account_file: str = Field(
        description="Path to Google service account JSON file"
    )
    spreadsheet_id: str = Field(
        default="1KKS89Y3M9xW6lI00qXAO45zyi7Xk5Y4DBGKqSDkfOZQ",
        description="Google Spreadsheet ID"
    )
    range_name: str = Field(
        default="Sheet1!A:M",
        description="Spreadsheet range to read"
    )
    timezone: str = Field(
        default="Europe/Dublin",
        description="Timezone for calendar events"
    )


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="SWAP_",
        env_file=".env",
        env_file_encoding="utf-8",
        yaml_file="config/config.yaml",
        yaml_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    # Application settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database configuration
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Google API configuration  
    google: GoogleConfig = Field(default_factory=GoogleConfig)
    
    # Users configuration
    users: List[UserConfig] = Field(
        default_factory=lambda: [
            UserConfig(
                calendar_name="Rachel's Rota",
                user_name="DrRachelKerry",
                emails_to_share=[
                    "madpin@gmail.com",
                    "tpinto@indeed.com", 
                    "rachelkerry95@gmail.com",
                    "rachiel.kerry1@gmail.com",
                ]
            ),
            UserConfig(
                calendar_name="Grace's Rota",
                user_name="DrGraceHigh",
                emails_to_share=["madpin@gmail.com"]
            )
        ]
    )
    
    def __init__(self, **kwargs):
        # Handle legacy SERVICE_ACCOUNT_FILE environment variable
        if "google" not in kwargs or not kwargs["google"].get("service_account_file"):
            service_account_file = os.environ.get("SERVICE_ACCOUNT_FILE")
            if service_account_file:
                if "google" not in kwargs:
                    kwargs["google"] = {}
                kwargs["google"]["service_account_file"] = service_account_file
        super().__init__(**kwargs)
    
    @field_validator("users")
    @classmethod
    def validate_users(cls, v):
        """Validate users configuration."""
        if not v:
            raise ValueError("At least one user must be configured")
        return v


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
