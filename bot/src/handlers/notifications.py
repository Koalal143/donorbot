from aiogram import F, Router
from aiogram.types import CallbackQuery
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from src.repositories.donor import DonorRepository
from src.services.notification_service import NotificationService

router = Router()


@inject
async def confirm_account_change_handler(
    callback: CallbackQuery,
    donor_repository: FromDishka[DonorRepository],
    notification_service: FromDishka[NotificationService],
) -> None:
    try:
        new_telegram_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка: неверные данные")
        return

    old_telegram_id = callback.from_user.id
    donor = await donor_repository.get_by_telegram_id(old_telegram_id)

    if not donor:
        await callback.answer("❌ Ошибка: донор не найден")
        return

    updated_donor = await donor_repository.update_telegram_id(donor.id, new_telegram_id)

    if updated_donor:
        await notification_service.send_account_change_confirmed(new_telegram_id, donor.full_name)

        await callback.answer("✅ Смена аккаунта подтверждена!")
        await callback.message.edit_text(
            f"✅ **Смена аккаунта подтверждена**\n\nАккаунт для пользователя **{donor.full_name}** успешно обновлен."
        )
    else:
        await callback.answer("❌ Ошибка при обновлении аккаунта")


@inject
async def reject_account_change_handler(
    callback: CallbackQuery,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    telegram_id = callback.from_user.id
    donor = await donor_repository.get_by_telegram_id(telegram_id)

    if not donor:
        await callback.answer("❌ Ошибка: донор не найден")
        return

    await callback.answer("❌ Смена аккаунта отклонена!")
    await callback.message.edit_text(
        f"❌ **Смена аккаунта отклонена**\n\nПопытка смены аккаунта для пользователя **{donor.full_name}** отклонена."
    )


router.callback_query.register(confirm_account_change_handler, F.data.startswith("confirm_account_change:"))
router.callback_query.register(reject_account_change_handler, F.data == "reject_account_change")
