from datetime import UTC, datetime
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import ProfileSG, RegistrationSG
from src.repositories.donor import DonorRepository


async def back_to_registration(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    # Получаем номер телефона для передачи обратно
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")

    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    await dialog_manager.start(RegistrationSG.account_access, data={"phone": phone})


@inject
async def get_profile_data(
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    # Получаем номер телефона из start_data или dialog_data
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")

    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    if not phone:
        return {
            "full_name": "Неизвестный пользователь",
            "donations_count": 0,
            "last_donation_date": "—",
            "last_donation_center": "—",
            "donations_history": "—",
            "total_blood_donated": "—",
        }

    donor = await donor_repository.get_by_phone_number(phone)

    if not donor:
        return {
            "full_name": "Пользователь не найден",
            "donations_count": 0,
            "last_donation_date": "—",
            "last_donation_center": "—",
            "donations_history": "—",
            "total_blood_donated": "—",
        }

    # Моковые данные
    mock_last_donation = datetime(1970, 1, 1, tzinfo=UTC)
    formatted_date = mock_last_donation.strftime("%d.%m.%Y")

    return {
        "full_name": donor.full_name,
        "donations_count": 0,
        "last_donation_date": formatted_date,
        "last_donation_center": "—",
        "donations_history": "—",
        "total_blood_donated": "—",
    }


profile_dialog = Dialog(
    Window(
        Format(
            "👤 **Профиль донора**\n\n"
            "📝 **ФИО:** {full_name}\n"
            "🩸 **Количество донаций:** {donations_count}\n"
            "📅 **Последняя донация:** {last_donation_date}\n"
            "🏥 **Центр последней донации:** {last_donation_center}\n"
            "📋 **История донаций:** {donations_history}\n"
            "🩸 **Всего крови сдано:** {total_blood_donated}"
        ),
        Button(
            Const("🔙 Назад"),
            id="back_button",
            on_click=back_to_registration,
        ),
        state=ProfileSG.profile_view,
        getter=get_profile_data,
    ),
)
