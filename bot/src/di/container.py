from dishka import make_async_container
from dishka.integrations.aiogram import AiogramProvider

from src.di.providers import (
    ConfigProvider,
    DatabaseProvider,
    RedisProvider,
    RepositoryProvider,
    TelegramBotProvider,
    WebhookProvider,
)

container = make_async_container(
    ConfigProvider(),
    DatabaseProvider(),
    RedisProvider(),
    RepositoryProvider(),
    AiogramProvider(),
    TelegramBotProvider(),
    WebhookProvider(),
)
