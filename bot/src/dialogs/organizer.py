from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Group, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.donor_add import (
    add_donors_handler,
    donor_add_input_handler,
    show_add_help,
)
from src.dialogs.donor_edit import (
    back_to_donor_data_management,
    back_to_donor_search,
    donor_edit_input_handler,
    donor_search_input_handler,
    donor_selected,
    edit_donor_data_handler,
    get_donor_edit_template_data,
    get_donor_selection_data,
    show_edit_help,
)
from src.dialogs.states import OrganizerSG
from src.dialogs.validators import (
    validate_organizer_name,
)
from src.models.donor_day import DonorDay
from src.models.organizer import Organizer
from src.repositories.content import ContentRepository
from src.repositories.donation import DonationRepository
from src.repositories.donor import DonorRepository
from src.repositories.donor_day import DonorDayRepository
from src.repositories.organizer import OrganizerRepository
from src.services.excel_generation_service import ExcelGenerationService
from src.services.notification_service import NotificationService


@inject
async def get_organizers_data(
    dialog_manager: DialogManager,
    organizer_repository: FromDishka[OrganizerRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    organizers = await organizer_repository.get_all()

    return {
        "organizers": [(org.id, org.name) for org in organizers],
        "has_organizers": len(organizers) > 0,
        "total_count": len(organizers),
    }


@inject
async def get_organizer_menu_data(
    dialog_manager: DialogManager,
    organizer_repository: FromDishka[OrganizerRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    selected_organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")
    organizer_name = "Неизвестный организатор"

    if selected_organizer_id:
        organizer = await organizer_repository.get_by_id(selected_organizer_id)
        if organizer:
            organizer_name = organizer.name

    return {
        "organizer_name": organizer_name,
    }


async def organizer_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    organizer_id = int(item_id)
    dialog_manager.dialog_data["selected_organizer_id"] = organizer_id

    await dialog_manager.switch_to(OrganizerSG.organizer_menu)


async def register_new_organizer(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await callback.answer("Переход к регистрации нового организатора...")
    await dialog_manager.switch_to(OrganizerSG.organizer_registration)


async def back_to_organizer_selection(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.organizer_selection)


async def events_management_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await callback.answer("Управление мероприятиями - в разработке")


async def donor_days_management_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_days_management)


async def donor_data_management_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_data_management)


async def statistics_management_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.statistics_management)


async def communication_management_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.communication_management)


@inject
async def organizer_name_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    organizer_repository: FromDishka[OrganizerRepository],
) -> None:
    validation_result = validate_organizer_name(data)
    if not validation_result.is_valid:
        await message.answer(validation_result.error_message)
        return

    name = data.strip()
    existing_organizer = await organizer_repository.get_by_name(name)
    if existing_organizer:
        await message.answer("Организатор с таким именем уже существует.")
        return

    new_organizer = Organizer(name=name)
    await organizer_repository.create(new_organizer)

    await message.answer(f"✅ Организатор '{name}' успешно зарегистрирован!")
    await dialog_manager.switch_to(OrganizerSG.organizer_selection)


async def create_donor_day_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_day_datetime_input)


async def view_donor_days_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_days_list)


@inject
async def cancel_donor_day_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    donor_day_repository: FromDishka[DonorDayRepository],
) -> None:
    donor_day_id = int(item_id)
    dialog_manager.dialog_data["selected_donor_day_id"] = donor_day_id

    donor_day = await donor_day_repository.get_by_id(donor_day_id)

    if donor_day:
        event_date = donor_day.event_datetime.strftime("%d.%m.%Y %H:%M")
        donor_day_info = f"День донора на {event_date}"
        dialog_manager.dialog_data["donor_day_info"] = donor_day_info

    await dialog_manager.switch_to(OrganizerSG.donor_day_cancel_confirmation)


@inject
async def confirm_cancel_donor_day(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donor_day_repository: FromDishka[DonorDayRepository],
    donation_repository: FromDishka[DonationRepository],
) -> None:
    donor_day_id = dialog_manager.dialog_data.get("selected_donor_day_id")

    if not donor_day_id:
        await callback.answer("Ошибка: не удалось получить данные дня донора")
        return

    donor_day = await donor_day_repository.get_by_id(donor_day_id)
    if not donor_day:
        await callback.answer("❌ Ошибка: день донора не найден")
        return

    donations_with_donors = await donation_repository.get_donations_with_donors_by_donor_day(donor_day_id)

    success = await donor_day_repository.delete_donor_day(donor_day_id)

    if success:
        if donations_with_donors:
            bot = dialog_manager.middleware_data.get("bot")
            if bot:
                notification_service = NotificationService(bot)

                notifications_data = []
                donor_day_date = donor_day.event_datetime.strftime("%d.%m.%Y %H:%M")

                for _donation, donor in donations_with_donors:
                    if donor.telegram_id:
                        notifications_data.append((donor.telegram_id, donor.full_name, donor_day_date, donor_day_id))

                if notifications_data:
                    stats = await notification_service.send_donor_day_cancelled_bulk(notifications_data)
                    await callback.answer(
                        f"✅ День донора отменен! Уведомления отправлены: {stats['success']} успешно, "
                        f"{stats['failed']} неудачно"
                    )
                else:
                    await callback.answer(
                        "✅ День донора отменен! Нет зарегистрированных пользователей для уведомления"
                    )
            else:
                await callback.answer("✅ День донора отменен! (Ошибка отправки уведомлений)")
        else:
            await callback.answer("✅ День донора отменен! Нет зарегистрированных пользователей")
    else:
        await callback.answer("❌ Ошибка при отмене дня донора")

    dialog_manager.dialog_data.pop("selected_donor_day_id", None)
    dialog_manager.dialog_data.pop("donor_day_info", None)

    await dialog_manager.switch_to(OrganizerSG.donor_days_list)


async def keep_donor_day(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data.pop("selected_donor_day_id", None)
    dialog_manager.dialog_data.pop("donor_day_info", None)

    await dialog_manager.switch_to(OrganizerSG.donor_days_list)


async def get_cancel_donor_day_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    donor_day_info = dialog_manager.dialog_data.get("donor_day_info", "Информация о дне донора недоступна")
    return {"donor_day_info": donor_day_info}


async def back_to_organizer_menu(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.organizer_menu)


@inject
async def donor_day_datetime_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    donor_day_repository: FromDishka[DonorDayRepository],
) -> None:
    try:
        naive_datetime = datetime.strptime(data.strip(), "%d.%m.%Y %H:%M")  # noqa: DTZ007

        moscow_tz = ZoneInfo("Europe/Moscow")
        event_datetime = naive_datetime.replace(tzinfo=moscow_tz)
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты и времени. Используйте формат ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2024 14:30)"
        )
        return

    organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")
    if not organizer_id:
        await message.answer("❌ Ошибка: организатор не выбран")
        return

    new_donor_day = DonorDay(
        event_datetime=event_datetime,
        organizer_id=organizer_id,
    )

    await donor_day_repository.create(new_donor_day)

    await message.answer(f"✅ День донора на {event_datetime.strftime('%d.%m.%Y %H:%M')} успешно создан!")
    await dialog_manager.switch_to(OrganizerSG.donor_days_management)


@inject
async def get_organizer_donor_days_data(
    dialog_manager: DialogManager,
    donor_day_repository: FromDishka[DonorDayRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")

    if not organizer_id:
        return {"donor_days": [], "has_donor_days": False, "use_scroll": False}

    donor_days = await donor_day_repository.get_by_organizer_id(organizer_id)

    if not donor_days:
        return {"donor_days": [], "has_donor_days": False, "use_scroll": False}
    donor_days_list = []

    for i, donor_day in enumerate(donor_days, 1):
        event_date = donor_day.event_datetime.strftime("%d.%m.%Y %H:%M")

        moscow_tz = ZoneInfo("Europe/Moscow")
        now_moscow = datetime.now(moscow_tz)

        if donor_day.event_datetime.tzinfo is None:
            event_moscow = donor_day.event_datetime.replace(tzinfo=moscow_tz)
        else:
            event_moscow = donor_day.event_datetime.astimezone(moscow_tz)

        status = "🟢 Активный" if event_moscow > now_moscow else "🔴 Прошедший"

        display_text = f"{i}. 📅 {event_date} - {status}"

        donor_days_list.append((donor_day.id, display_text))

    return {
        "donor_days": donor_days_list,
        "has_donor_days": len(donor_days_list) > 0,
        "use_scroll": len(donor_days_list) > 10,
    }


# Обработчики для рассылок
async def go_to_communication_management(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.communication_management)


async def go_to_mailing_category_selection(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.mailing_category_selection)


async def mailing_category_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["selected_mailing_category"] = item_id
    await dialog_manager.switch_to(OrganizerSG.mailing_message_input)


@inject
async def mailing_message_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    **kwargs: Any,
) -> None:
    message_text = data.strip()
    if not message_text:
        await message.answer("Сообщение не может быть пустым.")
        return

    if len(message_text) > 4000:
        await message.answer("Сообщение слишком длинное. Максимум 4000 символов.")
        return

    dialog_manager.dialog_data["mailing_message"] = message_text
    await dialog_manager.switch_to(OrganizerSG.mailing_confirmation)


@inject
async def send_mailing_confirmed(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
    organizer_repository: FromDishka[OrganizerRepository],
    notification_service: FromDishka[NotificationService],
) -> None:
    organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")
    category = dialog_manager.dialog_data.get("selected_mailing_category")
    message_text = dialog_manager.dialog_data.get("mailing_message")

    if not organizer_id or not category or not message_text:
        await callback.answer("Ошибка: не все данные заполнены")
        return

    organizer = await organizer_repository.get_by_id(organizer_id)
    if not organizer:
        await callback.answer("Ошибка: организатор не найден")
        return

    result = await notification_service.send_mailing_to_category(
        category=category,
        message_text=message_text,
        organizer_id=organizer_id,
        organizer_name=organizer.name,
        donor_repository=donor_repository,
    )

    success_count = result["success"]
    failed_count = result["failed"]

    await callback.answer(f"✅ Рассылка завершена!\nОтправлено: {success_count}\nОшибок: {failed_count}")

    await dialog_manager.switch_to(OrganizerSG.communication_management)


async def cancel_mailing(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.communication_management)


async def get_mailing_categories_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    categories = [
        ("upcoming_registered", "📅 Зарегистрированные на ближайшую дату ДД"),
        ("not_registered", "❌ Не зарегистрированные на ближайшие даты ДД"),
        ("registered_not_confirmed", "⏳ Зарегистрированные, но не подтвержденные"),
        ("bone_marrow", "🦴 Доноры костного мозга (ДКМ)"),
    ]

    return {
        "categories": categories,
        "has_categories": len(categories) > 0,
    }


async def get_mailing_confirmation_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    category = dialog_manager.dialog_data.get("selected_mailing_category", "")
    message_text = dialog_manager.dialog_data.get("mailing_message", "")

    category_names = {
        "upcoming_registered": "Зарегистрированные на ближайшую дату ДД",
        "not_registered": "Не зарегистрированные на ближайшие даты ДД",
        "registered_not_confirmed": "Зарегистрированные, но не подтвержденные",
        "bone_marrow": "Доноры костного мозга (ДКМ)",
    }

    category_name = category_names.get(category, "Неизвестная категория")

    return {
        "category_name": category_name,
        "message_text": message_text,
    }


# Обработчики для загрузки Excel
async def generate_excel_statistics(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.excel_generation_processing)


@inject
async def excel_generation_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    excel_service: FromDishka[ExcelGenerationService],
    donation_repository: FromDishka[DonationRepository],
    **kwargs: Any,
) -> None:
    organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")

    if not organizer_id:
        await callback.answer("❌ Ошибка: организатор не выбран")
        return

    await dialog_manager.switch_to(OrganizerSG.excel_generation_processing)

    # Показываем сообщение о начале генерации
    processing_msg = await callback.message.answer("⏳ Генерирую Excel файл со статистикой...")

    try:
        # Генерируем Excel файл асинхронно
        result = await excel_service.generate_statistics_excel(
            organizer_id=organizer_id, donation_repository=donation_repository
        )

        if not result["success"]:
            dialog_manager.dialog_data["excel_result"] = {
                "success": False,
                "error": result["error"],
                "records_count": 0,
            }
        else:
            # Отправляем файл пользователю
            file_content = result["file_content"]
            file_content.seek(0)  # Убеждаемся, что указатель в начале

            input_file = BufferedInputFile(file=file_content.read(), filename=result["filename"])

            await callback.message.answer_document(
                document=input_file, caption=f"📊 Статистика донорских дней\n📋 Записей: {result['records_count']}"
            )

            dialog_manager.dialog_data["excel_result"] = {
                "success": True,
                "records_count": result["records_count"],
                "filename": result["filename"],
            }

        await processing_msg.delete()
        await dialog_manager.switch_to(OrganizerSG.excel_generation_result)

    except Exception as e:
        await processing_msg.delete()
        dialog_manager.dialog_data["excel_result"] = {
            "success": False,
            "error": f"Ошибка генерации: {e!s}",
            "records_count": 0,
        }
        await dialog_manager.switch_to(OrganizerSG.excel_generation_result)


@inject
async def donors_excel_generation_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    excel_service: FromDishka[ExcelGenerationService],
    donation_repository: FromDishka[DonationRepository],
    **kwargs: Any,
) -> None:
    organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")

    if not organizer_id:
        await callback.answer("❌ Ошибка: организатор не выбран")
        return

    await dialog_manager.switch_to(OrganizerSG.donors_excel_generation_processing)

    # Показываем сообщение о начале генерации
    processing_msg = await callback.message.answer("⏳ Генерирую Excel файл со статистикой доноров...")

    try:
        # Генерируем Excel файл асинхронно
        result = await excel_service.generate_donors_excel(
            organizer_id=organizer_id, donation_repository=donation_repository
        )

        if not result["success"]:
            dialog_manager.dialog_data["donors_excel_result"] = {
                "success": False,
                "error": result["error"],
                "records_count": 0,
            }
        else:
            # Отправляем файл пользователю
            file_content = result["file_content"]
            file_content.seek(0)  # Убеждаемся, что указатель в начале

            input_file = BufferedInputFile(file=file_content.read(), filename=result["filename"])

            await callback.message.answer_document(
                document=input_file, caption=f"📊 Статистика доноров\n📋 Записей: {result['records_count']}"
            )

            dialog_manager.dialog_data["donors_excel_result"] = {
                "success": True,
                "records_count": result["records_count"],
                "filename": result["filename"],
            }

        await processing_msg.delete()
        await dialog_manager.switch_to(OrganizerSG.donors_excel_generation_result)

    except Exception as e:
        await processing_msg.delete()
        dialog_manager.dialog_data["donors_excel_result"] = {
            "success": False,
            "error": f"Ошибка генерации: {e!s}",
            "records_count": 0,
        }
        await dialog_manager.switch_to(OrganizerSG.donors_excel_generation_result)


async def get_excel_result_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    result = dialog_manager.dialog_data.get("excel_result", {})

    if result.get("success", False):
        result_message = (
            "✅ Файл успешно создан и отправлен!\n\n"
            f"📋 Записей в файле: {result.get('records_count', 0)}\n"
            f"📄 Имя файла: {result.get('filename', '')}\n\n"
            "Файл содержит статистику по всем донорским дням организатора с полями:\n"
            "• ДАТА ДД\n"
            "• ЦЕНТР КРОВИ\n"
            "• КОЛИЧЕСТВО ДОНОРОВ\n"
            "• КОЛИЧЕСТВО РЕГИСТРАЦИЙ"
        )
    else:
        result_message = f"❌ Ошибка генерации:\n{result.get('error', 'Неизвестная ошибка')}"

    return {
        "success": result.get("success", False),
        "error": result.get("error", ""),
        "records_count": result.get("records_count", 0),
        "filename": result.get("filename", ""),
        "result_message": result_message,
    }


async def get_donors_excel_result_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    result = dialog_manager.dialog_data.get("donors_excel_result", {})

    if result.get("success", False):
        result_message = (
            "✅ Файл со статистикой доноров успешно создан и отправлен!\n\n"
            f"📋 Записей в файле: {result.get('records_count', 0)}\n"
            f"📄 Имя файла: {result.get('filename', '')}\n\n"
            "Файл содержит данные всех подтвержденных донаций с полями:\n"
            "• ФИО\n"
            "• ДАТА\n"
            "• ОРГАНИЗАТОР (ЦК)"
        )
    else:
        result_message = f"❌ Ошибка генерации:\n{result.get('error', 'Неизвестная ошибка')}"

    return {
        "success": result.get("success", False),
        "error": result.get("error", ""),
        "records_count": result.get("records_count", 0),
        "filename": result.get("filename", ""),
        "result_message": result_message,
    }


async def back_to_statistics_from_excel(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    # Очищаем данные Excel из dialog_data
    dialog_manager.dialog_data.pop("excel_result", None)
    await dialog_manager.switch_to(OrganizerSG.statistics_management)


async def back_to_statistics_from_donors_excel(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    # Очищаем данные Excel доноров из dialog_data
    dialog_manager.dialog_data.pop("donors_excel_result", None)
    await dialog_manager.switch_to(OrganizerSG.statistics_management)


# Обработчики для редактирования прошедших ДД
@inject
async def get_past_donor_days_data(
    dialog_manager: DialogManager,
    donor_day_repository: FromDishka[DonorDayRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")
    if not organizer_id:
        return {"donor_days": []}

    donor_days = await donor_day_repository.get_past_by_organizer_id(organizer_id)
    donor_days_list = [
        (donor_day.id, f"{donor_day.event_datetime.strftime('%d.%m.%Y %H:%M')}") for donor_day in donor_days
    ]

    return {"donor_days": donor_days_list}


async def past_donor_day_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    **kwargs: Any,
) -> None:
    dialog_manager.dialog_data["selected_donor_day_id"] = int(item_id)
    await dialog_manager.switch_to(OrganizerSG.donor_day_participants)


@inject
async def get_participants_data(
    dialog_manager: DialogManager,
    donation_repository: FromDishka[DonationRepository],
    donor_day_repository: FromDishka[DonorDayRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    donor_day_id = dialog_manager.dialog_data.get("selected_donor_day_id")
    if not donor_day_id:
        return {"participants": [], "donor_day_info": ""}

    # Получаем информацию о донорском дне
    donor_day = await donor_day_repository.get_by_id(donor_day_id)
    donor_day_info = f"{donor_day.event_datetime.strftime('%d.%m.%Y %H:%M')}" if donor_day else ""

    # Получаем участников
    participants = await donation_repository.get_participants_by_donor_day(donor_day_id)

    participants_list = []
    for p in participants:
        status_icons = []
        if p["is_confirmed"]:
            status_icons.append("✅")
        if p["is_bone_marrow_donor"]:
            status_icons.append("🦴")

        status_text = " ".join(status_icons) if status_icons else "❌"

        participants_list.append((p["donation_id"], f"{p['donor_name']} - {status_text}"))

    return {
        "participants": participants_list,
        "donor_day_info": donor_day_info,
    }


async def participant_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    **kwargs: Any,
) -> None:
    dialog_manager.dialog_data["selected_donation_id"] = int(item_id)
    await dialog_manager.switch_to(OrganizerSG.edit_participant_status)


@inject
async def get_participant_status_data(
    dialog_manager: DialogManager,
    donation_repository: FromDishka[DonationRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    donation_id = dialog_manager.dialog_data.get("selected_donation_id")
    if not donation_id:
        return {"participant_info": "", "is_confirmed": False, "is_bone_marrow_donor": False}

    # Получаем информацию об участнике
    participants = await donation_repository.get_participants_by_donor_day(
        dialog_manager.dialog_data.get("selected_donor_day_id")
    )

    participant = next((p for p in participants if p["donation_id"] == donation_id), None)
    if not participant:
        return {"participant_info": "", "is_confirmed": False, "is_bone_marrow_donor": False}

    return {
        "participant_info": f"{participant['donor_name']} ({participant['phone_number']})",
        "is_confirmed": participant["is_confirmed"],
        "is_bone_marrow_donor": participant["is_bone_marrow_donor"],
        "show_bone_marrow_button": not participant["is_bone_marrow_donor"],
        "blood_status_text": "✅ Да" if participant["is_confirmed"] else "❌ Нет",
        "bone_marrow_status_text": "✅ Да" if participant["is_bone_marrow_donor"] else "❌ Нет",
        "toggle_blood_text": "Отменить" if participant["is_confirmed"] else "Подтвердить",
    }


@inject
async def toggle_blood_donation_status(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donation_repository: FromDishka[DonationRepository],
    **kwargs: Any,
) -> None:
    donation_id = dialog_manager.dialog_data.get("selected_donation_id")
    if not donation_id:
        return

    # Получаем текущий статус
    participants = await donation_repository.get_participants_by_donor_day(
        dialog_manager.dialog_data.get("selected_donor_day_id")
    )
    participant = next((p for p in participants if p["donation_id"] == donation_id), None)
    if not participant:
        return

    # Переключаем статус
    new_status = not participant["is_confirmed"]
    await donation_repository.update_donation_status(donation_id, new_status)

    await callback.answer(f"Статус сдачи крови: {'✅ Сдал' if new_status else '❌ Не сдал'}")


@inject
async def toggle_bone_marrow_status(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donation_repository: FromDishka[DonationRepository],
    donor_repository: FromDishka[DonorRepository],
    **kwargs: Any,
) -> None:
    donation_id = dialog_manager.dialog_data.get("selected_donation_id")
    if not donation_id:
        return

    # Получаем информацию об участнике
    participants = await donation_repository.get_participants_by_donor_day(
        dialog_manager.dialog_data.get("selected_donor_day_id")
    )
    participant = next((p for p in participants if p["donation_id"] == donation_id), None)
    if not participant:
        return

    # Переключаем статус костного мозга (только включение, выключение не предусмотрено)
    if not participant["is_bone_marrow_donor"]:
        await donor_repository.update_bone_marrow_status(participant["donor_id"], True)
        await callback.answer("✅ Донор добавлен в регистр костного мозга!")
    else:
        await callback.answer("ℹ️ Донор уже в регистре костного мозга")


async def go_to_add_participant(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.participant_phone_input)


async def participant_phone_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    **kwargs: Any,
) -> None:
    # Простая валидация номера телефона
    phone = data.strip()
    if len(phone) < 10:
        await message.answer("❌ Введите корректный номер телефона")
        return

    dialog_manager.dialog_data["new_participant_phone"] = phone
    await dialog_manager.switch_to(OrganizerSG.add_participant)


async def get_add_participant_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    phone = dialog_manager.dialog_data.get("new_participant_phone", "")
    return {"phone": phone}


@inject
async def create_participant_by_phone(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    donor_repository: FromDishka[DonorRepository],
    donation_repository: FromDishka[DonationRepository],
    **kwargs: Any,
) -> None:
    phone = dialog_manager.dialog_data.get("new_participant_phone")
    donor_day_id = dialog_manager.dialog_data.get("selected_donor_day_id")

    if not phone or not donor_day_id:
        await callback.answer("❌ Ошибка: недостаточно данных")
        return

    try:
        # Ищем донора по номеру телефона
        donor = await donor_repository.get_by_phone_number(phone)

        if not donor:
            await callback.answer("❌ Донор с таким номером не найден в системе")
            return

        # Проверяем, не зарегистрирован ли уже на этот день
        existing_donation = await donation_repository.get_by_donor_and_donor_day(donor.id, donor_day_id)
        if existing_donation:
            await callback.answer("⚠️ Донор уже зарегистрирован на этот день")
            return

        # Создаем регистрацию
        await donation_repository.create_donation(donor.id, donor_day_id)

        await callback.answer(f"✅ Донор {donor.full_name} добавлен к участникам")

        # Очищаем данные и возвращаемся к списку участников
        dialog_manager.dialog_data.pop("new_participant_phone", None)
        await dialog_manager.switch_to(OrganizerSG.donor_day_participants)

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e!s}")


async def cancel_add_participant(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data.pop("new_participant_phone", None)
    await dialog_manager.switch_to(OrganizerSG.donor_day_participants)


# Обработчики для управления контентом
@inject
async def get_content_list_data(
    dialog_manager: DialogManager,
    content_repository: FromDishka[ContentRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")
    if not organizer_id:
        return {"content_items": []}

    content_items = await content_repository.get_by_organizer_id(organizer_id)
    content_list = [
        (content.id, f"{content.title[:50]}{'...' if len(content.title) > 50 else ''}") for content in content_items
    ]

    return {"content_items": content_list}


async def content_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    **kwargs: Any,
) -> None:
    dialog_manager.dialog_data["selected_content_id"] = int(item_id)
    await dialog_manager.switch_to(OrganizerSG.content_view)


@inject
async def get_content_view_data(
    dialog_manager: DialogManager,
    content_repository: FromDishka[ContentRepository],
    **kwargs: Any,
) -> dict[str, Any]:
    content_id = dialog_manager.dialog_data.get("selected_content_id")
    if not content_id:
        return {"title": "", "description": ""}

    content = await content_repository.get_by_id(content_id)
    if not content:
        return {"title": "", "description": ""}

    return {
        "title": content.title,
        "description": content.description,
    }


async def content_title_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    **kwargs: Any,
) -> None:
    title = data.strip()
    if len(title) < 3:
        await message.answer("❌ Название должно содержать минимум 3 символа")
        return
    if len(title) > 200:
        await message.answer("❌ Название не должно превышать 200 символов")
        return

    dialog_manager.dialog_data["new_content_title"] = title
    await dialog_manager.switch_to(OrganizerSG.content_add_description)


async def content_description_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    **kwargs: Any,
) -> None:
    description = data.strip()
    if len(description) < 10:
        await message.answer("❌ Описание должно содержать минимум 10 символов")
        return
    if len(description) > 4000:
        await message.answer("❌ Описание не должно превышать 4000 символов")
        return

    dialog_manager.dialog_data["new_content_description"] = description
    await dialog_manager.switch_to(OrganizerSG.content_confirm)


async def get_content_confirm_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    title = dialog_manager.dialog_data.get("new_content_title", "")
    description = dialog_manager.dialog_data.get("new_content_description", "")

    return {
        "title": title,
        "description": description[:300] + "..." if len(description) > 300 else description,
    }


@inject
async def create_content_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    content_repository: FromDishka[ContentRepository],
    **kwargs: Any,
) -> None:
    title = dialog_manager.dialog_data.get("new_content_title")
    description = dialog_manager.dialog_data.get("new_content_description")
    organizer_id = dialog_manager.dialog_data.get("selected_organizer_id")

    if not title or not description or not organizer_id:
        await callback.answer("❌ Ошибка: недостаточно данных")
        return

    try:
        from src.models.content import Content

        new_content = Content(title=title, description=description, organizer_id=organizer_id)

        await content_repository.create(new_content)

        # Очищаем данные
        dialog_manager.dialog_data.pop("new_content_title", None)
        dialog_manager.dialog_data.pop("new_content_description", None)

        await callback.answer("✅ Контент успешно создан!")
        await dialog_manager.switch_to(OrganizerSG.content_list)

    except Exception as e:
        await callback.answer(f"❌ Ошибка создания: {e!s}")


@inject
async def delete_content_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    content_repository: FromDishka[ContentRepository],
    **kwargs: Any,
) -> None:
    content_id = dialog_manager.dialog_data.get("selected_content_id")
    if not content_id:
        await callback.answer("❌ Контент не выбран")
        return

    try:
        success = await content_repository.delete(content_id)
        if success:
            await callback.answer("✅ Контент удален!")
            dialog_manager.dialog_data.pop("selected_content_id", None)
            await dialog_manager.switch_to(OrganizerSG.content_list)
        else:
            await callback.answer("❌ Контент не найден")
    except Exception as e:
        await callback.answer(f"❌ Ошибка удаления: {e!s}")


async def cancel_content_creation(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data.pop("new_content_title", None)
    dialog_manager.dialog_data.pop("new_content_description", None)
    await dialog_manager.switch_to(OrganizerSG.content_management)


organizer_dialog = Dialog(
    Window(
        Format("Выберите, какой из организаторов вы:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="organizers",
                item_id_getter=lambda item: str(item[0]),
                id="organizer_select",
                on_click=organizer_selected,
            ),
            id="organizers_scroll",
            width=1,
            height=4,
            when="has_organizers",
        ),
        Const("В базе данных нет организаторов.", when="!has_organizers"),
        Button(
            Const("➕ Зарегистрировать нового организатора"),
            id="register_organizer",
            on_click=register_new_organizer,
        ),
        state=OrganizerSG.organizer_selection,
        getter=get_organizers_data,
    ),
    Window(
        Const("Введите ФИО нового организатора:"),
        TextInput(
            id="organizer_name_input",
            on_success=organizer_name_input_handler,
        ),
        state=OrganizerSG.organizer_registration,
    ),
    Window(
        Format(
            "🎛️ Панель управления организатора\n\n👤 Выбранный организатор: {organizer_name}\n\n"
            "Выберите отдел для управления:"
        ),
        Group(
            Row(
                Button(
                    Const("📅 Мероприятия"),
                    id="events_management",
                    on_click=events_management_handler,
                ),
            ),
            Row(
                Button(
                    Const("🩸 Дни донора"),
                    id="donor_days_management",
                    on_click=donor_days_management_handler,
                ),
                Button(
                    Const("👥 Данные доноров"),
                    id="donor_data_management",
                    on_click=donor_data_management_handler,
                ),
            ),
            Row(
                Button(
                    Const("📊 Статистика"),
                    id="statistics_management",
                    on_click=statistics_management_handler,
                ),
                Button(
                    Const("� Контент"),
                    id="content_management_btn",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.content_management),
                ),
                Button(
                    Const("�💬 Коммуникации"),
                    id="communication_management",
                    on_click=communication_management_handler,
                ),
            ),
        ),
        Button(
            Const("🔙 Назад к выбору организатора"),
            id="back_to_selection",
            on_click=back_to_organizer_selection,
        ),
        state=OrganizerSG.organizer_menu,
        getter=get_organizer_menu_data,
    ),
    Window(
        Const(
            "📅 Управление мероприятиями\n\n• Создание мероприятий\n• "
            "Редактирование мероприятий\n• Управление расписанием"
        ),
        Button(
            Const("🔙 Назад в меню"),
            id="back_to_menu",
            on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
        ),
        state=OrganizerSG.events_management,
    ),
    Window(
        Const(
            "🩸 Управление днями донора\n\n• Создание новых дней донора\n• "
            "Просмотр существующих дней донора\n• Управление регистрациями"
        ),
        Group(
            Row(
                Button(
                    Const("➕ Создать день донора"),
                    id="create_donor_day",
                    on_click=create_donor_day_handler,
                ),
                Button(
                    Const("📋 Просмотр дней донора"),
                    id="view_donor_days",
                    on_click=view_donor_days_handler,
                ),
            ),
            Row(
                Button(
                    Const("✏️ Редактировать прошедшие ДД"),
                    id="edit_past_donor_days",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.past_donor_days_list),
                ),
            ),
        ),
        Button(
            Const("🔙 Назад в меню"),
            id="back_to_menu",
            on_click=back_to_organizer_menu,
        ),
        state=OrganizerSG.donor_days_management,
    ),
    Window(
        Const("📅 Введите дату и время проведения дня донора в формате ДД.ММ.ГГГГ ЧЧ:ММ:"),
        TextInput(
            id="donor_day_datetime_input",
            on_success=donor_day_datetime_input_handler,
        ),
        Button(
            Const("🔙 Назад к управлению"),
            id="back_to_donor_days_management_from_input",
            on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.donor_days_management),
        ),
        state=OrganizerSG.donor_day_datetime_input,
    ),
    Window(
        Const("🩸 Дни донора организатора"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="donor_days",
                item_id_getter=lambda item: str(item[0]),
                id="donor_day_select_scroll",
                on_click=cancel_donor_day_selected,
            ),
            id="donor_days_scroll",
            width=1,
            height=5,
            when="has_donor_days",
        ),
        Const("У вас пока нет созданных дней донора.", when="!has_donor_days"),
        Group(
            Row(
                Button(
                    Const("🔙 Назад к управлению"),
                    id="back_to_donor_days_management",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.donor_days_management),
                ),
            ),
        ),
        state=OrganizerSG.donor_days_list,
        getter=get_organizer_donor_days_data,
    ),
    Window(
        Format("❓ Отмена дня донора\n\n{donor_day_info}\n\nВы уверены, что хотите отменить этот день донора?"),
        Group(
            Row(
                Button(
                    Const("✅ Да, отменить"),
                    id="confirm_cancel_donor_day",
                    on_click=confirm_cancel_donor_day,
                ),
                Button(
                    Const("❌ Нет, оставить"),
                    id="keep_donor_day",
                    on_click=keep_donor_day,
                ),
            ),
        ),
        state=OrganizerSG.donor_day_cancel_confirmation,
        getter=get_cancel_donor_day_data,
    ),
    Window(
        Const(
            "👥 Управление данными доноров\n\n• Редактирование данных доноров\n• "
            "Добавление данных доноров\n• Поиск и фильтрация"
        ),
        Group(
            Row(
                Button(
                    Const("✏️ Редактировать данные донора"),
                    id="edit_donor_data",
                    on_click=edit_donor_data_handler,
                ),
                Button(
                    Const("➕ Добавить доноров"),
                    id="add_donors",
                    on_click=add_donors_handler,
                ),
            ),
        ),
        Button(
            Const("🔙 Назад в меню"),
            id="back_to_menu",
            on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
        ),
        state=OrganizerSG.donor_data_management,
    ),
    Window(
        Const("📊 Управление статистикой\n\nВыберите действие:"),
        Group(
            Row(
                Button(
                    Const("📊 Статистика ДД"),
                    id="generate_excel",
                    on_click=excel_generation_handler,
                ),
                Button(
                    Const("👥 Статистика доноров"),
                    id="generate_donors_excel",
                    on_click=donors_excel_generation_handler,
                ),
            ),
            Row(
                Button(
                    Const("🔙 Назад в меню"),
                    id="back_to_menu",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
                ),
            ),
        ),
        state=OrganizerSG.statistics_management,
    ),
    Window(
        Const("🔍 Поиск донора для редактирования\n\nВведите ФИО или номер телефона донора:"),
        TextInput(
            id="donor_search_input",
            on_success=donor_search_input_handler,
        ),
        Button(
            Const("🔙 Назад к управлению данными"),
            id="back_to_donor_data_management",
            on_click=back_to_donor_data_management,
        ),
        state=OrganizerSG.donor_search_input,
    ),
    Window(
        Const("👥 Выберите донора\n\nНайдено несколько доноров с похожими данными:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="donors",
                item_id_getter=lambda item: str(item[0]),
                id="donor_select",
                on_click=donor_selected,
            ),
            id="donors_scroll",
            width=1,
            height=5,
            when="has_donors",
        ),
        Const("Доноры не найдены.", when="!has_donors"),
        Button(
            Const("🔙 Назад к поиску"),
            id="back_to_search",
            on_click=back_to_donor_search,
        ),
        state=OrganizerSG.donor_selection,
        getter=get_donor_selection_data,
    ),
    Window(
        Format("👤 Редактирование данных донора: {donor_name}\n\n{template}"),
        TextInput(
            id="donor_edit_input",
            on_success=donor_edit_input_handler,
        ),
        Group(
            Row(
                Button(
                    Const("❓ Помощь"),
                    id="show_edit_help",
                    on_click=show_edit_help,
                ),
                Button(
                    Const("🔙 Назад к поиску"),
                    id="back_to_search_from_template",
                    on_click=back_to_donor_search,
                ),
            ),
            Row(
                Button(
                    Const("🏠 К управлению данными"),
                    id="back_to_management_from_template",
                    on_click=back_to_donor_data_management,
                ),
            ),
        ),
        state=OrganizerSG.donor_edit_template,
        getter=get_donor_edit_template_data,
    ),
    Window(
        Const(
            "❓ Помощь по редактированию данных доноров\n\n"
            "📝 Формат данных для редактирования:\n\n"
            "ФИО: Фамилия Имя Отчество\n"
            "• Только буквы (русские или латинские)\n"
            "• Минимум 2 слова (фамилия и имя)\n"
            "• Максимум 4 слова\n"
            "• Каждое слово от 2 до 30 букв\n"
            "• Пример: `Иванов Иван Иванович`\n\n"
            "Телефон: Номер телефона\n"
            "• Российский номер (начинается с 7 или 8)\n"
            "• От 10 до 11 цифр\n"
            "• Можно использовать +, -, (, ), пробелы\n"
            "• Примеры: `+79123456789`, `8-912-345-67-89`, `7 (912) 345-67-89`\n\n"
            "Тип: Тип донора\n"
            "• `студент` - для студентов (обязательно указать группу)\n"
            "• `сотрудник` - для сотрудников учреждения\n"
            "• `внешний` - для внешних доноров\n\n"
            "Группа: Студенческая группа (только для студентов)\n"
            "• Буквы, цифры, дефисы и точки\n"
            "• От 2 до 20 символов\n"
            "• Примеры: `ИТ-21`, `МЕД-3А`, `ЭК.19`\n\n"
            "📋 Пример правильного заполнения:\n"
            "```\n"
            "ФИО: Петров Петр Петрович\n"
            "Телефон: +79123456789\n"
            "Тип: студент\n"
            "Группа: ИТ-21\n"
            "```\n\n"
            "⚠️ Важно:\n"
            "• Сохраняйте формат `Поле: Значение`\n"
            "• Каждое поле на новой строке\n"
            "• Не изменяйте названия полей\n"
            "• Для сотрудников и внешних доноров группу не указывайте"
        ),
        Group(
            Row(
                Button(
                    Const("🔙 Назад к редактированию"),
                    id="back_to_edit_template",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.donor_edit_template),
                ),
                Button(
                    Const("🏠 К управлению данными"),
                    id="back_to_management_from_help",
                    on_click=back_to_donor_data_management,
                ),
            ),
        ),
        state=OrganizerSG.donor_edit_help,
    ),
    Window(
        Const(
            "➕ Добавление новых доноров\n\n"
            "Введите данные доноров в следующем формате.\n"
            "Для добавления нескольких доноров разделяйте их пустой строкой:\n\n"
            "📋 Пример для одного донора:\n"
            "```\n"
            "ФИО: Иванов Иван Иванович\n"
            "Телефон: +79123456789\n"
            "Тип: студент\n"
            "Группа: ИТ-21\n"
            "```\n\n"
            "📋 Пример для нескольких доноров:\n"
            "```\n"
            "ФИО: Иванов Иван Иванович\n"
            "Телефон: +79123456789\n"
            "Тип: студент\n"
            "Группа: ИТ-21\n\n"
            "ФИО: Петров Петр Петрович\n"
            "Телефон: +79987654321\n"
            "Тип: сотрудник\n"
            "```\n\n"
            "⚠️ Важно: Добавлять можно только пользователей, которые уже зарегистрированы в боте!"
        ),
        TextInput(
            id="donor_add_input",
            on_success=donor_add_input_handler,
        ),
        Group(
            Row(
                Button(
                    Const("❓ Помощь"),
                    id="show_add_help",
                    on_click=show_add_help,
                ),
                Button(
                    Const("🔙 Назад к управлению"),
                    id="back_to_management_from_add",
                    on_click=back_to_donor_data_management,
                ),
            ),
        ),
        state=OrganizerSG.donor_add_input,
    ),
    Window(
        Const(
            "❓ Помощь по добавлению доноров\n\n"
            "📝 Формат данных для добавления:\n\n"
            "ФИО: Фамилия Имя Отчество\n"
            "• Только буквы (русские или латинские)\n"
            "• Минимум 2 слова (фамилия и имя)\n"
            "• Максимум 4 слова\n"
            "• Каждое слово от 2 до 30 букв\n"
            "• Пример: `Иванов Иван Иванович`\n\n"
            "Телефон: Номер телефона\n"
            "• Российский номер (начинается с 7 или 8)\n"
            "• От 10 до 11 цифр\n"
            "• Можно использовать +, -, (, ), пробелы\n"
            "• Примеры: `+79123456789`, `8-912-345-67-89`, `7 (912) 345-67-89`\n\n"
            "Тип: Тип донора\n"
            "• `студент` - для студентов (обязательно указать группу)\n"
            "• `сотрудник` - для сотрудников учреждения\n"
            "• `внешний` - для внешних доноров\n\n"
            "Группа: Студенческая группа (только для студентов)\n"
            "• Буквы, цифры, дефисы и точки\n"
            "• От 2 до 20 символов\n"
            "• Примеры: `ИТ-21`, `МЕД-3А`, `ЭК.19`\n\n"
            "📋 Множественное добавление:\n"
            "• Разделяйте данные разных доноров пустой строкой\n"
            "• Каждый донор должен содержать все обязательные поля\n"
            "• Обработка происходит последовательно\n"
            "• При ошибке в одном доноре, остальные все равно обрабатываются\n\n"
            "📋 Пример множественного добавления:\n"
            "```\n"
            "ФИО: Иванов Иван Иванович\n"
            "Телефон: +79123456789\n"
            "Тип: студент\n"
            "Группа: ИТ-21\n\n"
            "ФИО: Петров Петр Петрович\n"
            "Телефон: +79987654321\n"
            "Тип: сотрудник\n\n"
            "ФИО: Сидоров Сидор Сидорович\n"
            "Телефон: +79111111111\n"
            "Тип: внешний\n"
            "```\n\n"
            "⚠️ Ограничения:\n"
            "• Можно добавлять только зарегистрированных пользователей\n"
            "• Пользователь не должен быть донором\n"
            "• Сохраняйте формат `Поле: Значение`\n"
            "• Не изменяйте названия полей"
        ),
        Group(
            Row(
                Button(
                    Const("🔙 Назад к добавлению"),
                    id="back_to_add_input",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.donor_add_input),
                ),
                Button(
                    Const("🏠 К управлению данными"),
                    id="back_to_management_from_add_help",
                    on_click=back_to_donor_data_management,
                ),
            ),
        ),
        state=OrganizerSG.donor_add_help,
    ),
    Window(
        Const("📢 Управление рассылками\n\nВыберите действие:"),
        Group(
            Row(
                Button(
                    Const("📤 Создать рассылку"),
                    id="create_mailing",
                    on_click=go_to_mailing_category_selection,
                ),
            ),
            Row(
                Button(
                    Const("🔙 Назад к меню"),
                    id="back_to_organizer_menu_from_communication",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
                ),
            ),
        ),
        state=OrganizerSG.communication_management,
    ),
    Window(
        Const("📋 Выбор категории получателей\n\nВыберите категорию доноров для рассылки:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="categories",
                item_id_getter=lambda item: item[0],
                id="category_select",
                on_click=mailing_category_selected,
            ),
            id="categories_scroll",
            width=1,
            height=4,
            when="has_categories",
        ),
        Group(
            Row(
                Button(
                    Const("🔙 Назад"),
                    id="back_to_communication_management",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.communication_management),
                ),
            ),
        ),
        state=OrganizerSG.mailing_category_selection,
        getter=get_mailing_categories_data,
    ),
    Window(
        Const("✍️ Введите текст сообщения\n\nНапишите сообщение, которое будет отправлено выбранной категории доноров:"),
        TextInput(
            id="mailing_message_input",
            on_success=mailing_message_input_handler,
        ),
        Group(
            Row(
                Button(
                    Const("🔙 Назад"),
                    id="back_to_category_selection",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.mailing_category_selection),
                ),
            ),
        ),
        state=OrganizerSG.mailing_message_input,
    ),
    Window(
        Format(
            "📋 Подтверждение рассылки\n\n"
            "Категория получателей: {category_name}\n\n"
            "Текст сообщения:\n{message_text}\n\n"
            "Отправить рассылку?"
        ),
        Group(
            Row(
                Button(
                    Const("✅ Отправить"),
                    id="confirm_send_mailing",
                    on_click=send_mailing_confirmed,
                ),
                Button(
                    Const("❌ Отменить"),
                    id="cancel_mailing",
                    on_click=cancel_mailing,
                ),
            ),
        ),
        state=OrganizerSG.mailing_confirmation,
        getter=get_mailing_confirmation_data,
    ),
    Window(
        Const("⏳ Генерация Excel файла...\n\nПожалуйста, подождите."),
        state=OrganizerSG.excel_generation_processing,
    ),
    Window(
        Format("📊 Результат генерации Excel файла\n\n{result_message}"),
        Group(
            Row(
                Button(
                    Const("🔙 Назад к статистике"),
                    id="back_to_statistics_from_result",
                    on_click=back_to_statistics_from_excel,
                ),
            ),
        ),
        state=OrganizerSG.excel_generation_result,
        getter=get_excel_result_data,
    ),
    Window(
        Const("⏳ Генерация Excel файла со статистикой доноров...\n\nПожалуйста, подождите."),
        state=OrganizerSG.donors_excel_generation_processing,
    ),
    Window(
        Format("📊 Результат генерации Excel файла со статистикой доноров\n\n{result_message}"),
        Group(
            Row(
                Button(
                    Const("🔙 Назад к статистике"),
                    id="back_to_statistics_from_donors_result",
                    on_click=back_to_statistics_from_donors_excel,
                ),
            ),
        ),
        state=OrganizerSG.donors_excel_generation_result,
        getter=get_donors_excel_result_data,
    ),
    # Окна для редактирования прошедших ДД
    Window(
        Const("✏️ Редактирование прошедших донорских дней\n\nВыберите донорский день для редактирования:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="donor_days",
                item_id_getter=lambda item: str(item[0]),
                id="past_donor_day_select",
                on_click=past_donor_day_selected,
            ),
            id="past_donor_days_scroll",
            width=1,
            height=5,
        ),
        Group(
            Row(
                Button(
                    Const("🔙 Назад в меню"),
                    id="back_to_organizer_menu_from_past",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
                ),
            ),
        ),
        state=OrganizerSG.past_donor_days_list,
        getter=get_past_donor_days_data,
    ),
    Window(
        Format("👥 Участники донорского дня\n\n📅 {donor_day_info}\n\nСписок участников:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="participants",
                item_id_getter=lambda item: str(item[0]),
                id="participant_select",
                on_click=participant_selected,
            ),
            id="participants_scroll",
            width=1,
            height=5,
        ),
        Group(
            Row(
                Button(
                    Const("➕ Добавить участника"),
                    id="add_participant_btn",
                    on_click=go_to_add_participant,
                ),
            ),
            Row(
                Button(
                    Const("🔙 К списку ДД"),
                    id="back_to_past_donor_days",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.past_donor_days_list),
                ),
            ),
        ),
        state=OrganizerSG.donor_day_participants,
        getter=get_participants_data,
    ),
    Window(
        Const("📱 Добавление участника\n\nВведите номер телефона донора:"),
        TextInput(
            id="participant_phone_input",
            on_success=participant_phone_input_handler,
        ),
        Group(
            Row(
                Button(
                    Const("🔙 Отмена"),
                    id="cancel_add_participant",
                    on_click=cancel_add_participant,
                ),
            ),
        ),
        state=OrganizerSG.participant_phone_input,
    ),
    Window(
        Format("➕ Подтверждение добавления\n\nТелефон: {phone}\n\nДобавить участника?"),
        Group(
            Row(
                Button(
                    Const("✅ Добавить"),
                    id="confirm_add_participant",
                    on_click=create_participant_by_phone,
                ),
                Button(
                    Const("❌ Отмена"),
                    id="cancel_add_participant_confirm",
                    on_click=cancel_add_participant,
                ),
            ),
        ),
        state=OrganizerSG.add_participant,
        getter=get_add_participant_data,
    ),
    Window(
        Format(
            "✏️ Редактирование статуса участника\n\n"
            "👤 {participant_info}\n\n"
            "Текущий статус:\n"
            "🩸 Сдал кровь: {blood_status_text}\n"
            "🦴 Регистр костного мозга: {bone_marrow_status_text}"
        ),
        Group(
            Row(
                Button(
                    Format("🩸 {toggle_blood_text} донацию"),
                    id="toggle_blood_donation",
                    on_click=toggle_blood_donation_status,
                ),
            ),
            Row(
                Button(
                    Const("🦴 Добавить в регистр КМ"),
                    id="toggle_bone_marrow",
                    on_click=toggle_bone_marrow_status,
                ),
                when="show_bone_marrow_button",
            ),
            Row(
                Button(
                    Const("🔙 К участникам"),
                    id="back_to_participants",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.donor_day_participants),
                ),
            ),
        ),
        state=OrganizerSG.edit_participant_status,
        getter=get_participant_status_data,
    ),
    # Окна для управления контентом
    Window(
        Const("📄 Управление контентом\n\nВыберите действие:"),
        Group(
            Row(
                Button(
                    Const("📋 Просмотр контента"),
                    id="view_content_list",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.content_list),
                ),
                Button(
                    Const("➕ Добавить контент"),
                    id="add_content",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.content_add_title),
                ),
            ),
            Row(
                Button(
                    Const("🔙 Назад в меню"),
                    id="back_to_organizer_menu_from_content",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
                ),
            ),
        ),
        state=OrganizerSG.content_management,
    ),
    Window(
        Const("📋 Список контента\n\nВыберите статью для просмотра:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                items="content_items",
                item_id_getter=lambda item: str(item[0]),
                id="content_select",
                on_click=content_selected,
            ),
            id="content_scroll",
            width=1,
            height=5,
        ),
        Group(
            Row(
                Button(
                    Const("➕ Добавить контент"),
                    id="add_content_from_list",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.content_add_title),
                ),
            ),
            Row(
                Button(
                    Const("🔙 К управлению контентом"),
                    id="back_to_content_management",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.content_management),
                ),
            ),
        ),
        state=OrganizerSG.content_list,
        getter=get_content_list_data,
    ),
    Window(
        Format("📄 {title}\n\n{description}"),
        Group(
            Row(
                Button(
                    Const("🗑️ Удалить"),
                    id="delete_content",
                    on_click=delete_content_handler,
                ),
            ),
            Row(
                Button(
                    Const("🔙 К списку контента"),
                    id="back_to_content_list",
                    on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.content_list),
                ),
            ),
        ),
        state=OrganizerSG.content_view,
        getter=get_content_view_data,
    ),
    Window(
        Const("📝 Добавление контента\n\nВведите название статьи:"),
        TextInput(
            id="content_title_input",
            on_success=content_title_input_handler,
        ),
        Group(
            Row(
                Button(
                    Const("❌ Отмена"),
                    id="cancel_content_creation",
                    on_click=cancel_content_creation,
                ),
            ),
        ),
        state=OrganizerSG.content_add_title,
    ),
    Window(
        Const("📝 Добавление контента\n\nВведите содержимое статьи:"),
        TextInput(
            id="content_description_input",
            on_success=content_description_input_handler,
        ),
        Group(
            Row(
                Button(
                    Const("❌ Отмена"),
                    id="cancel_content_creation_desc",
                    on_click=cancel_content_creation,
                ),
            ),
        ),
        state=OrganizerSG.content_add_description,
    ),
    Window(
        Format(
            "✅ Подтверждение создания контента\n\n"
            "📄 Название: {title}\n\n"
            "📝 Содержимое:\n{description}\n\n"
            "Создать статью?"
        ),
        Group(
            Row(
                Button(
                    Const("✅ Создать"),
                    id="confirm_create_content",
                    on_click=create_content_handler,
                ),
                Button(
                    Const("❌ Отмена"),
                    id="cancel_content_creation_confirm",
                    on_click=cancel_content_creation,
                ),
            ),
        ),
        state=OrganizerSG.content_confirm,
        getter=get_content_confirm_data,
    ),
)
