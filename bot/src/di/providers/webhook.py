from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp.web import Application, AppRunner
from aiohttp.web_runner import TCPSite
from dishka import Provider, Scope, provide

from src.core.config import Settings


class WebhookProvider(Provider):
    scope = Scope.APP

    @provide
    def get_web_app(self) -> Application:
        return Application()

    @provide
    def get_simple_request_handler(self, settings: Settings, bot: Bot, dispatcher: Dispatcher) -> SimpleRequestHandler:
        return SimpleRequestHandler(
            dispatcher=dispatcher,
            bot=bot,
            secret_token=settings.telegram_bot.token.get_secret_value(),
        )

    @provide
    def get_app_runner(self, web_app: Application) -> AppRunner:
        return AppRunner(web_app)

    @provide
    def get_site(self, app_runner: AppRunner, settings: Settings) -> TCPSite:
        return TCPSite(app_runner, host=settings.telegram_bot.webhook_host, port=settings.telegram_bot.webhook_port)
