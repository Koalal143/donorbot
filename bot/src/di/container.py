from dishka import make_async_container
from dishka.integrations.aiogram import AiogramProvider

from src.di.providers import ConfigProvider, TelegramBotProvider

container = make_async_container(
    ConfigProvider(),
    AiogramProvider(),
    TelegramBotProvider(),
)
