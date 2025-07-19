from datetime import UTC, datetime
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Group, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import DonorDayMenuSG, ProfileSG
from src.repositories.donation import DonationRepository
from src.repositories.donor import DonorRepository
from src.repositories.donor_day import DonorDayRepository
from src.repositories.organizer import OrganizerRepository


@inject
async def get_profile_data(
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
    donation_repository: FromDishka[DonationRepository],
    organizer_repository: FromDishka[OrganizerRepository],
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
            "bone_marrow_registry": "—",
        }

    donor = await donor_repository.get_by_phone_number(phone)

    if not donor:
        return {
            "full_name": "Пользователь не найден",
            "donations_count": 0,
            "last_donation_date": "—",
            "last_donation_center": "—",
            "bone_marrow_registry": "—",
        }

    all_donations = await donation_repository.get_donor_registrations_with_details(donor.id)

    confirmed_donations = [donation for donation, _ in all_donations if donation.is_confirmed]
    donations_count = len(confirmed_donations)

    last_donation_date = "—"
    last_donation_center = "—"

    if confirmed_donations:
        confirmed_with_dates = [(donation, donor_day) for donation, donor_day in all_donations if donation.is_confirmed]
        confirmed_with_dates.sort(key=lambda x: x[1].event_datetime, reverse=True)

        if confirmed_with_dates:
            last_donation, last_donor_day = confirmed_with_dates[0]
            last_donation_date = last_donor_day.event_datetime.strftime("%d.%m.%Y")

            organizer = await organizer_repository.get_by_id(last_donation.organizer_id)
            last_donation_center = organizer.name if organizer else "Неизвестный центр"

    bone_marrow_registry = "Не вступил"

    return {
        "full_name": donor.full_name,
        "donations_count": donations_count,
        "last_donation_date": last_donation_date,
        "last_donation_center": last_donation_center,
        "bone_marrow_registry": bone_marrow_registry,
        "donor_id": donor.id,
    }


@inject
async def get_my_registrations_data(
    dialog_manager: DialogManager,
    donation_repository: FromDishka[DonationRepository],
    donor_repository: FromDishka[DonorRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    if not phone:
        return {"registrations": [], "has_registrations": False, "use_scroll": False}

    donor = await donor_repository.get_by_phone_number(phone)

    if not donor:
        return {"registrations": [], "has_registrations": False, "use_scroll": False}

    registrations = await donation_repository.get_donor_registrations_with_details(donor.id)

    if not registrations:
        return {"registrations": [], "has_registrations": False, "use_scroll": False}

    registrations_list = []

    for i, (donation, donor_day) in enumerate(registrations, 1):
        if donation.is_confirmed:
            continue

        event_date = donor_day.event_datetime.strftime("%d.%m.%Y %H:%M")

        now = datetime.now(UTC)
        can_cancel = donor_day.event_datetime > now

        display_text = f"{i}. 📅 {event_date}"

        if can_cancel:
            registrations_list.append((donation.id, f"{display_text}\n ❌ Нажмите для отмены"))
        else:
            registrations_list.append((donation.id, f"{display_text}\n ⚠️ Нельзя отменить (прошедшая дата)"))

    return {
        "registrations": registrations_list,
        "has_registrations": len(registrations_list) > 0,
        "use_scroll": len(registrations_list) > 10,
    }


@inject
async def confirm_cancel_registration(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donation_repository: FromDishka[DonationRepository],
    donor_repository: FromDishka[DonorRepository],
) -> None:
    donation_id = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        donation_id = dialog_manager.start_data.get("selected_donation_id")

    if not donation_id:
        await callback.answer("Ошибка: не удалось получить данные регистрации")
        return

    # Проверяем, что регистрация все еще существует
    donation = await donation_repository.get_by_id(donation_id)
    if not donation:
        await callback.answer("Ошибка: регистрация не найдена")

        phone = None
        if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
            phone = dialog_manager.start_data.get("phone")
        if not phone:
            phone = dialog_manager.dialog_data.get("phone")

        await dialog_manager.start(ProfileSG.my_registrations, data={"phone": phone})
        return

    success = await donation_repository.delete_donation(donation_id)

    if success:
        await callback.answer("✅ Регистрация успешно отменена!")
    else:
        await callback.answer("❌ Ошибка при отмене регистрации")

    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    await dialog_manager.start(ProfileSG.my_registrations, data={"phone": phone})


@inject
async def cancel_registration_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    donation_repository: FromDishka[DonationRepository],
    donor_day_repository: FromDishka[DonorDayRepository],
) -> None:
    donation_id = int(item_id)

    donation = await donation_repository.get_by_id(donation_id)

    if not donation:
        await callback.answer("Ошибка: регистрация не найдена")
        return

    donor_day = await donor_day_repository.get_by_id(donation.donor_day_id)

    if donor_day:
        event_date = donor_day.event_datetime.strftime("%d.%m.%Y %H:%M")
        registration_info = f"Регистрация на день донора: {event_date}"
    else:
        registration_info = "Регистрация на день донора"

    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    await dialog_manager.start(
        ProfileSG.cancel_registration,
        data={"phone": phone, "selected_donation_id": donation_id, "registration_info": registration_info},
    )


async def keep_registration(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    await dialog_manager.start(ProfileSG.my_registrations, data={"phone": phone})


async def get_cancel_registration_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    registration_info = "Информация о регистрации недоступна"
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        registration_info = dialog_manager.start_data.get("registration_info", "Информация о регистрации недоступна")
    return {"registration_info": registration_info}


async def donation_item_click(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    await callback.answer()


@inject
async def get_donation_history_data(
    dialog_manager: DialogManager,
    donation_repository: FromDishka[DonationRepository],
    donor_repository: FromDishka[DonorRepository],
    organizer_repository: FromDishka[OrganizerRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")
    if not phone:
        phone = dialog_manager.dialog_data.get("phone")

    if not phone:
        return {"donations": [], "has_donations": False, "use_scroll": False}

    donor = await donor_repository.get_by_phone_number(phone)

    if not donor:
        return {"donations": [], "has_donations": False, "use_scroll": False}

    donor_donations = await donation_repository.get_donor_donations_with_details(donor.id)

    if not donor_donations:
        return {"donations": [], "has_donations": False, "use_scroll": False}

    donations_list = []
    for i, (donation, donor_day) in enumerate(donor_donations, 1):
        date_str = donor_day.event_datetime.strftime("%d.%m.%Y")
        status = "✅ Подтверждена" if donation.is_confirmed else "⏳ Ожидает подтверждения"

        organizer = await organizer_repository.get_by_id(donation.organizer_id)
        center_name = organizer.name if organizer else "Неизвестный центр"

        donations_list.append((donation.id, f"{i}. 📅 {date_str} - {center_name} - {status}"))

    return {
        "donations": donations_list,
        "has_donations": len(donations_list) > 0,
        "use_scroll": len(donations_list) > 10,
    }


async def go_to_donor_day_menu(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")

    await dialog_manager.start(DonorDayMenuSG.menu, data={"phone": phone})


async def go_to_my_registrations(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")

    await dialog_manager.start(ProfileSG.my_registrations, data={"phone": phone})


async def go_to_donation_history(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    phone = None
    if dialog_manager.start_data and isinstance(dialog_manager.start_data, dict):
        phone = dialog_manager.start_data.get("phone")

    await dialog_manager.start(ProfileSG.donation_history, data={"phone": phone})


profile_dialog = Dialog(
    Window(
        Format(
            "👤 **Профиль донора**\n\n"
            "📝 **ФИО:** {full_name}\n"
            "🩸 **Количество донаций:** {donations_count}\n"
            "📅 **Последняя донация:** {last_donation_date}\n"
            "🏥 **Центр последней донации:** {last_donation_center}\n"
            "🦴 **Вступил в регистр доноров костного мозга:** {bone_marrow_registry}"
        ),
        Group(
            Row(
                Button(
                    Const("🩸 День донора"),
                    id="donor_day_menu",
                    on_click=go_to_donor_day_menu,
                ),
            ),
        ),
        state=ProfileSG.profile_view,
        getter=get_profile_data,
    ),
    Window(
        Const("📋 **Мои регистрации на Дни донора**"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="registrations",
                item_id_getter=lambda item: str(item[0]),
                id="registration_select_scroll",
                on_click=cancel_registration_selected,
            ),
            id="registrations_scroll",
            width=1,
            height=5,
            when="has_registrations",
        ),
        Const("У вас пока нет регистраций на Дни донора.", when="!has_registrations"),
        Group(
            Row(
                Button(
                    Const("🔙 Назад к меню"),
                    id="back_to_donor_day_menu",
                    on_click=go_to_donor_day_menu,
                ),
            ),
        ),
        state=ProfileSG.my_registrations,
        getter=get_my_registrations_data,
    ),
    Window(
        Format("❓ **Отмена регистрации**\n\n{registration_info}\n\nВы уверены, что хотите отменить регистрацию?"),
        Group(
            Row(
                Button(
                    Const("✅ Да, отменить"),
                    id="confirm_cancel",
                    on_click=confirm_cancel_registration,
                ),
                Button(
                    Const("❌ Нет, оставить"),
                    id="keep_registration",
                    on_click=keep_registration,
                ),
            ),
        ),
        state=ProfileSG.cancel_registration,
        getter=get_cancel_registration_data,
    ),
    Window(
        Const("📊 **История донаций**"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="donations",
                item_id_getter=lambda item: str(item[0]),
                id="donation_select_scroll",
                on_click=donation_item_click,
            ),
            id="donations_scroll",
            width=1,
            height=5,
            when="has_donations",
        ),
        Const("У вас пока нет донаций.", when="!has_donations"),
        Group(
            Row(
                Button(
                    Const("🔙 Назад к меню"),
                    id="back_to_donor_day_menu",
                    on_click=go_to_donor_day_menu,
                ),
            ),
        ),
        state=ProfileSG.donation_history,
        getter=get_donation_history_data,
    ),
)
