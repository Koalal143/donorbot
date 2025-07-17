import asyncio

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp.web import Application, AppRunner
from aiohttp.web_runner import TCPSite
from dishka import AsyncContainer

from src.core.config import Settings
from src.di.container import container
from src.handlers import main_router
from src.lifespan import on_shutdown, on_startup


async def setup_webhook(container: AsyncContainer) -> None:
    settings: Settings = await container.get(Settings)
    bot: Bot = await container.get(Bot)
    dp: Dispatcher = await container.get(Dispatcher)
    app: Application = await container.get(Application)
    webhook_requests_handler: SimpleRequestHandler = await container.get(SimpleRequestHandler)
    runner: AppRunner = await container.get(AppRunner)

    if (
        not settings.telegram_bot.webhook_url
        or not settings.telegram_bot.webhook_path
        or not settings.telegram_bot.webhook_secret_token
    ):
        msg = "webhook_url or webhook_path or webhook_secret_token is not set"
        raise ValueError(msg)

    await bot.set_webhook(
        settings.telegram_bot.webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        secret_token=settings.telegram_bot.webhook_secret_token.get_secret_value(),
    )

    webhook_requests_handler.register(app, path=settings.telegram_bot.webhook_path)
    setup_application(app, dp, bot=bot)

    await runner.setup()

    site: TCPSite = await container.get(TCPSite)
    await site.start()
    await asyncio.Event().wait()


async def main() -> None:
    settings: Settings = await container.get(Settings)

    dp: Dispatcher = await container.get(Dispatcher)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_router(main_router)

    if settings.telegram_bot.use_webhook:
        await setup_webhook(container)
    else:
        bot: Bot = await container.get(Bot)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
