from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject
from aiogram_dialog.api.exceptions import UnknownIntent


class DialogErrorHandlerMiddleware(BaseMiddleware):
    """Middleware для обработки ошибок диалогов"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except UnknownIntent:
            # Если это callback query, отвечаем пользователю
            if isinstance(event, CallbackQuery):
                await event.answer(
                    "⚠️ Сессия диалога устарела. Используйте команду /start для начала работы.", show_alert=True
                )
                # Можно также отправить новое сообщение с инструкциями
                await event.message.answer(
                    "🔄 Сессия была сброшена. Пожалуйста, используйте команду /start для продолжения работы."
                )
            return None
        except Exception:
            # Логируем другие ошибки, но не ломаем бота
            if isinstance(event, CallbackQuery):
                await event.answer("❌ Произошла ошибка. Попробуйте использовать команду /start.", show_alert=True)
            return None
