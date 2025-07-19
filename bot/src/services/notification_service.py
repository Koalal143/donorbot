from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class NotificationService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_account_change_notification(
        self, old_telegram_id: int, full_name: str, new_telegram_id: int
    ) -> bool:
        message_text = (
            f"⚠️ **Уведомление о смене аккаунта**\n\n"
            f"Пользователь **{full_name}** пытается войти в систему с нового аккаунта.\n\n"
            f"Новый Telegram ID: `{new_telegram_id}`\n\n"
            f"Если это вы, можете подтвердить смену аккаунта."
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить смену аккаунта",
                        callback_data=f"confirm_account_change:{new_telegram_id}",
                    )
                ],
                [InlineKeyboardButton(text="❌ Отклонить", callback_data="reject_account_change")],
            ]
        )

        await self.bot.send_message(
            chat_id=old_telegram_id, text=message_text, reply_markup=keyboard, parse_mode="Markdown"
        )
        return True

    async def send_account_change_confirmed(self, new_telegram_id: int, full_name: str) -> bool:
        message_text = (
            f"✅ **Смена аккаунта подтверждена**\n\n"
            f"Аккаунт для пользователя **{full_name}** успешно обновлен.\n\n"
            f"Теперь вы можете использовать все функции системы."
        )

        await self.bot.send_message(chat_id=new_telegram_id, text=message_text, parse_mode="Markdown")
        return True

    async def send_account_change_rejected(self, new_telegram_id: int, full_name: str) -> bool:
        message_text = (
            f"❌ **Смена аккаунта отклонена**\n\n"
            f"Попытка смены аккаунта для пользователя **{full_name}** была отклонена.\n\n"
            f"Пожалуйста, используйте оригинальный аккаунт для входа в систему."
        )

        await self.bot.send_message(chat_id=new_telegram_id, text=message_text, parse_mode="Markdown")
        return True

    async def send_donor_day_cancelled_notification(
        self,
        telegram_id: int,
        donor_name: str,
        donor_day_date: str,
    ) -> bool:
        message_text = (
            f"❌ **День донора отменен**\n\n"
            f"Уважаемый **{donor_name}**!\n\n"
            f"День донора, запланированный на **{donor_day_date}**, был отменен организатором.\n\n"
            f"Ваша регистрация автоматически аннулирована.\n\n"
            f"Вы можете записаться на другие дни донора в разделе '📅 Записаться на День донора'."
        )

        await self.bot.send_message(chat_id=telegram_id, text=message_text, parse_mode="Markdown")
        return True

    async def send_donor_day_cancelled_bulk(
        self, notifications_data: list[tuple[int, str, str, int]]
    ) -> dict[str, int]:
        success_count = 0
        failed_count = 0

        for telegram_id, donor_name, donor_day_date, _ in notifications_data:
            success = await self.send_donor_day_cancelled_notification(telegram_id, donor_name, donor_day_date)
            if success:
                success_count += 1
            else:
                failed_count += 1

        return {"success": success_count, "failed": failed_count}
