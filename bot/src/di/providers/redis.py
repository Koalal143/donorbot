from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from src.core.config import settings


class RedisProvider(Provider):
    scope = Scope.APP

    @provide
    def get_redis(self) -> Redis:
        return Redis.from_url(settings.redis.url.get_secret_value())
