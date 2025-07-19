from aiogram import Bot
from dishka import Provider, Scope, provide

from src.services.excel_generation_service import ExcelGenerationService
from src.services.notification_service import NotificationService


class ServicesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_excel_generation_service(self, bot: Bot) -> ExcelGenerationService:
        return ExcelGenerationService(bot)

    @provide(scope=Scope.REQUEST)
    def get_notification_service(self, bot: Bot) -> NotificationService:
        return NotificationService(bot)
