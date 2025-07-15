from pathlib import Path
from typing import Literal

from pydantic import BaseModel, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PATH = Path(__file__).parent.parent


class TelegramBotSettings(BaseModel):
    token: SecretStr
    use_webhook: bool = False
    webhook_base_url: str | None = None
    webhook_path: str | None = None

    @field_validator("use_webhook")
    @classmethod
    def validate_use_webhook(cls, v: bool, values: ValidationInfo) -> bool:  # noqa: FBT001
        if v and not (values.data.get("webhook_base_url") and values.data.get("webhook_path")):
            msg = "webhook_base_url and webhook_path fields are required when use_webhook is True"
            raise ValueError(msg)
        return v

    @property
    def webhook_url(self) -> str | None:
        if self.use_webhook:
            return f"{self.webhook_base_url}{self.webhook_path}"
        return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=PATH / ".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    telegram_bot: TelegramBotSettings
    mode: Literal["dev", "prod", "test"] = "prod"


settings = Settings()
