from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Group, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import DonorDayMenuSG, DonorDayRegistrationSG
from src.models.donation import Donation
from src.repositories.donation import DonationRepository
from src.repositories.donor_day import DonorDayRepository


@inject
async def get_donor_days_data(
    dialog_manager: DialogManager,
    donor_day_repository: FromDishka[DonorDayRepository],
    donation_repository: FromDishka[DonationRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    donor_days = await donor_day_repository.get_all_upcoming()

    if not donor_days:
        return {
            "donor_days": [],
            "message": "К сожалению, ближайших Дней донора не запланировано.",
        }

    donor_id = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        donor_id = dialog_manager.start_data.get("donor_id")

    available_donor_days = []
    for donor_day in donor_days:
        if donor_id:
            existing_registration = await donation_repository.get_donor_registration(donor_id, donor_day.id)
            if not existing_registration:
                available_donor_days.append(donor_day)
        else:
            available_donor_days.append(donor_day)

    if not available_donor_days:
        return {
            "donor_days": [],
            "message": "Вы уже зарегистрированы на все доступные Дни донора.",
        }

    donor_days_list = [
        (donor_day.id, f"📅 {donor_day.event_datetime.strftime('%d.%m.%Y %H:%M')}")
        for donor_day in available_donor_days
    ]

    return {
        "donor_days": donor_days_list,
        "message": "Выберите День донора для регистрации:",
    }


@inject
async def get_donor_day_details_data(
    dialog_manager: DialogManager,
    donor_day_repository: FromDishka[DonorDayRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    donor_day_id = dialog_manager.dialog_data.get("selected_donor_day_id")

    if not donor_day_id:
        return {"error": "День донора не выбран"}

    donor_day = await donor_day_repository.get_by_id(donor_day_id)

    if not donor_day:
        return {"error": "День донора не найден"}

    return {
        "donor_day_id": donor_day.id,
        "event_datetime": donor_day.event_datetime.strftime("%d.%m.%Y %H:%M"),
    }


async def donor_day_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["selected_donor_day_id"] = int(item_id)
    await dialog_manager.switch_to(DonorDayRegistrationSG.registration_confirmation)


@inject
async def confirm_registration(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donation_repository: FromDishka[DonationRepository],
    donor_day_repository: FromDishka[DonorDayRepository],
) -> None:
    donor_day_id = dialog_manager.dialog_data.get("selected_donor_day_id")
    donor_id = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        donor_id = dialog_manager.start_data.get("donor_id")

    if not donor_day_id or not donor_id:
        await callback.answer("Ошибка: не удалось получить данные для регистрации")
        return

    donor_day = await donor_day_repository.get_by_id(donor_day_id)
    if not donor_day:
        await callback.answer("Ошибка: день донора не найден")
        return

    existing_registration = await donation_repository.get_donor_registration(donor_id, donor_day_id)

    if existing_registration:
        await callback.answer("Вы уже зарегистрированы на этот День донора!")
        return

    new_donation = Donation(
        donor_id=donor_id,
        organizer_id=donor_day.organizer_id,
        donor_day_id=donor_day_id,
        is_confirmed=False,
    )

    await donation_repository.create(new_donation)

    await callback.answer("✅ Вы успешно зарегистрированы на День донора!")

    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")

    await dialog_manager.start(DonorDayMenuSG.menu, data={"phone": phone})


async def back_to_profile(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")

    await dialog_manager.start(DonorDayMenuSG.menu, data={"phone": phone})


async def cancel_registration(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await callback.answer("Регистрация отменена")

    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")

    await dialog_manager.start(DonorDayMenuSG.menu, data={"phone": phone})


donor_day_registration_dialog = Dialog(
    Window(
        Format("{message}"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="donor_days",
                item_id_getter=lambda item: str(item[0]),
                id="donor_day_select",
                on_click=donor_day_selected,
            ),
            id="donor_days_scroll",
            width=1,
            height=5,
        ),
        Button(
            Const("🔙 Назад к меню"),
            id="back_to_profile",
            on_click=back_to_profile,
        ),
        state=DonorDayRegistrationSG.donor_days_list,
        getter=get_donor_days_data,
    ),
    Window(
        Format("📅 День донора\n\n📅 Дата и время: {event_datetime}\n\nПодтвердите регистрацию на этот День донора:"),
        Group(
            Row(
                Button(
                    Const("✅ Подтвердить"),
                    id="confirm_registration",
                    on_click=confirm_registration,
                ),
                Button(
                    Const("❌ Отменить"),
                    id="cancel_registration",
                    on_click=cancel_registration,
                ),
            ),
        ),
        state=DonorDayRegistrationSG.registration_confirmation,
        getter=get_donor_day_details_data,
    ),
)
