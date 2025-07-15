from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PATH = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=PATH / ".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    telegram_bot_token: SecretStr
    mode: Literal["dev", "prod", "test"] = "prod"


settings = Settings()
