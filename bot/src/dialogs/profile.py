from datetime import UTC, datetime
from typing import Any

from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.text import Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import ProfileSG
from src.repositories.donor import DonorRepository


@inject
async def get_profile_data(
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
    **kwargs: Any,
) -> dict[str, Any]:
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
            "bone_marrow_registry": "—",
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
            "bone_marrow_registry": "—",
        }

    mock_last_donation = datetime(1970, 1, 1, tzinfo=UTC)
    formatted_date = mock_last_donation.strftime("%d.%m.%Y")

    return {
        "full_name": donor.full_name,
        "donations_count": 0,
        "last_donation_date": formatted_date,
        "last_donation_center": "—",
        "donations_history": "—",
        "total_blood_donated": "—",
        "bone_marrow_registry": "—",
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
            "🩸 **Всего крови сдано:** {total_blood_donated}\n"
            "🦴 **Вступил в регистр доноров костного мозга:** {bone_marrow_registry}"
        ),
        state=ProfileSG.profile_view,
        getter=get_profile_data,
    ),
)
