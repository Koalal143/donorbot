from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from src.core.config import Settings


class TelegramBotProvider(Provider):
    scope = Scope.APP

    @provide
    def get_redis_storage(self, redis: Redis) -> RedisStorage:
        return RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_destiny=True))

    @provide
    def get_bot(self, settings: Settings) -> Bot:
        return Bot(
            token=settings.telegram_bot.token.get_secret_value(),
            default=DefaultBotProperties(parse_mode=None),
        )

    @provide
    def get_dispatcher(self, bot: Bot, redis_storage: RedisStorage) -> Dispatcher:
        return Dispatcher(bot=bot, storage=redis_storage)
