from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from taskiq_redis import RedisScheduleSource

from src.di.container import container


async def on_startup() -> None:
    redis_source: RedisScheduleSource = await container.get(RedisScheduleSource)
    await redis_source.startup()

    redis: Redis = await container.get(Redis)
    await redis.ping()


async def on_shutdown() -> None:
    bot: Bot = await container.get(Bot)
    await bot.delete_webhook()
    await bot.session.close()

    redis: Redis = await container.get(Redis)
    await redis.aclose()

    database_engine: AsyncEngine = await container.get(AsyncEngine)
    await database_engine.dispose()
