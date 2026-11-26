"""Application configuration loaded from environment variables or .env file."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for eeclass-mcp."""

    model_config = SettingsConfigDict(
        env_prefix="EECLASS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = Field(
        default="https://ncueeclass.ncu.edu.tw",
        description="Base URL of the NCU ee-class server.",
    )
    username: str = Field(
        default="",
        description="ee-class account username / student ID.",
    )
    password: SecretStr = Field(
        default=SecretStr(""),
        description="ee-class account password.",
    )
    download_dir: Path = Field(
        default=Path("downloads"),
        description="Local directory where downloaded attachments are saved.",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level written to stderr.",
    )
    headless: bool = Field(
        default=True,
        description="Whether Playwright launches Chromium in headless mode.",
    )
    login_lock_file: Path = Field(
        default=Path("LOGIN_FAILED"),
        description="Written after a rejected login; while it exists, login is not attempted.",
    )
    request_timeout: float = Field(
        default=30.0,
        gt=0,
        description="HTTP request timeout in seconds.",
    )
