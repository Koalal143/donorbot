from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from src.core.config import Settings


class TelegramBotProvider(Provider):
    scope = Scope.APP

    @provide
    def get_redis_storage(self, redis: Redis) -> RedisStorage:
        return RedisStorage(redis=redis)

    @provide
    def get_bot(self, settings: Settings) -> Bot:
        return Bot(token=settings.telegram_bot.token.get_secret_value())

    @provide
    def get_dispatcher(self, bot: Bot) -> Dispatcher:
        return Dispatcher(bot=bot)
