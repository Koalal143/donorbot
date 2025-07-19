from aiogram import Bot, Dispatcher
from aiogram_dialog import setup_dialogs
from dishka.integrations.aiogram import setup_dishka
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from src.di.container import container
from src.scheduling.source import redis_source


async def on_startup() -> None:
    await redis_source.startup()

    redis: Redis = await container.get(Redis)
    await redis.ping()

    dp: Dispatcher = await container.get(Dispatcher)
    setup_dishka(container, dp, auto_inject=True)
    setup_dialogs(dp)


async def on_shutdown() -> None:
    bot: Bot = await container.get(Bot)
    await bot.delete_webhook()
    await bot.session.close()

    redis: Redis = await container.get(Redis)
    await redis.aclose()

    database_engine: AsyncEngine = await container.get(AsyncEngine)
    await database_engine.dispose()
