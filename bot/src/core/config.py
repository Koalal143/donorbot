from pathlib import Path
from typing import Literal

from pydantic import BaseModel, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PATH = Path(__file__).parent.parent


class PostgresConfig(BaseModel):
    user: str
    password: SecretStr
    host: str
    port: int
    db: str
    echo: bool = False
    naming_convention: dict = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @property
    def url(self) -> SecretStr:
        return SecretStr(
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"
        )


class RedisConfig(BaseModel):
    uri_scheme: Literal["redis", "rediss"] = "redis"
    host: str
    port: int
    user: str | None
    password: SecretStr | None
    db: int

    @property
    def url(self) -> SecretStr:
        if self.user and not self.password:
            msg = "Password is required when user is provided"
            raise ValueError(msg)
        if self.user and self.password:
            return SecretStr(
                f"{self.uri_scheme}://{self.user or ''}:{self.password.get_secret_value()}@{self.host}:{self.port}"
                f"/{self.db}"
            )
        return SecretStr(f"{self.uri_scheme}://{self.host}:{self.port}/{self.db}")


class TelegramBotSettings(BaseModel):
    token: SecretStr
    use_webhook: bool = False
    webhook_base_url: str | None = None
    webhook_path: str | None = None
    webhook_host: str | None = None
    webhook_port: int | None = None

    @field_validator("use_webhook", mode="after")
    @classmethod
    def validate_use_webhook(cls, v: bool, values: ValidationInfo) -> bool:  # noqa: FBT001
        neccessary_fields = ["webhook_base_url", "webhook_path", "webhook_host", "webhook_port"]
        unset_fields = [field for field in neccessary_fields if not values.data.get(field)]
        if v and unset_fields:
            msg = f"The following fields are required when use_webhook is True: {', '.join(unset_fields)}"
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

    postgres: PostgresConfig
    redis: RedisConfig
    telegram_bot: TelegramBotSettings
    mode: Literal["dev", "prod", "test"] = "prod"


settings = Settings()
