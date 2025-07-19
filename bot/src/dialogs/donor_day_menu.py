from aiogram import types
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Group, Row
from aiogram_dialog.widgets.text import Const
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import DonorDayMenuSG, DonorDayRegistrationSG, ProfileSG
from src.repositories.donor import DonorRepository


@inject
async def go_to_donor_day_registration(
    callback: types.CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    if not phone:
        await callback.answer("Ошибка: не удалось получить данные пользователя")
        return

    donor = await donor_repository.get_by_phone_number(phone)
    if not donor:
        await callback.answer("Ошибка: пользователь не найден")
        return

    await dialog_manager.start(DonorDayRegistrationSG.donor_days_list, data={"donor_id": donor.id, "phone": phone})


@inject
async def go_to_my_registrations(
    callback: types.CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    if not phone:
        await callback.answer("Ошибка: не удалось получить данные пользователя")
        return

    await dialog_manager.start(ProfileSG.my_registrations, data={"phone": phone})


@inject
async def go_to_donation_history(
    callback: types.CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    if not phone:
        await callback.answer("Ошибка: не удалось получить данные пользователя")
        return

    await dialog_manager.start(ProfileSG.donation_history, data={"phone": phone})


async def back_to_profile(
    callback: types.CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    if not phone:
        await callback.answer("Ошибка: не удалось получить данные пользователя")
        return

    await dialog_manager.start(ProfileSG.profile_view, data={"phone": phone})


donor_day_menu_dialog = Dialog(
    Window(
        Const("🩸 Меню Дня донора\n\nВыберите действие:"),
        Group(
            Row(
                Button(
                    Const("📅 Записаться на День донора"),
                    id="register_for_donor_day",
                    on_click=go_to_donor_day_registration,
                ),
            ),
            Row(
                Button(
                    Const("📋 Мои регистрации"),
                    id="my_registrations",
                    on_click=go_to_my_registrations,
                ),
            ),
            Row(
                Button(
                    Const("📊 История донаций"),
                    id="donation_history",
                    on_click=go_to_donation_history,
                ),
            ),
            Row(
                Button(
                    Const("🔙 Назад к профилю"),
                    id="back_to_profile",
                    on_click=back_to_profile,
                ),
            ),
        ),
        state=DonorDayMenuSG.menu,
    ),
)
