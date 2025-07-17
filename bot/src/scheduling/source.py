from taskiq_redis import ListRedisScheduleSource

from src.core.config import settings

redis_source = ListRedisScheduleSource(settings.redis.url.get_secret_value())
