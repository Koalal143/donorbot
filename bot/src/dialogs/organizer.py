from datetime import UTC, datetime
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Group, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import OrganizerSG
from src.dialogs.validators import validate_organizer_name
from src.models.donor_day import DonorDay
from src.models.organizer import Organizer
from src.repositories.donation import DonationRepository
from src.repositories.donor_day import DonorDayRepository
from src.repositories.organizer import OrganizerRepository
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


async def content_management_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await callback.answer("Управление контентом - в разработке")


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
    await callback.answer("Управление данными доноров - в разработке")


async def statistics_management_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await callback.answer("Управление статистикой - в разработке")


async def communication_management_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await callback.answer("Управление коммуникациями - в разработке")


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
        event_datetime = datetime.strptime(data.strip(), "%d.%m.%Y %H:%M")  # noqa: DTZ007
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
        now = datetime.now(UTC)
        status = "🟢 Активный" if donor_day.event_datetime > now else "🔴 Прошедший"

        display_text = f"{i}. 📅 {event_date} - {status}"

        donor_days_list.append((donor_day.id, display_text))

    return {
        "donor_days": donor_days_list,
        "has_donor_days": len(donor_days_list) > 0,
        "use_scroll": len(donor_days_list) > 10,
    }


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
            "🎛️ **Панель управления организатора**\n\n👤 **Выбранный организатор:** {organizer_name}\n\n"
            "Выберите отдел для управления:"
        ),
        Group(
            Row(
                Button(
                    Const("📅 Мероприятия"),
                    id="events_management",
                    on_click=events_management_handler,
                ),
                Button(
                    Const("📝 Контент"),
                    id="content_management",
                    on_click=content_management_handler,
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
                    Const("💬 Коммуникации"),
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
            "📅 **Управление мероприятиями**\n\n• Создание мероприятий\n• "
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
            "📝 **Управление контентом**\n\n• Редактирование информации о донорстве\n• "
            "Обновление текстов и описаний\n• Управление FAQ"
        ),
        Button(
            Const("🔙 Назад в меню"),
            id="back_to_menu",
            on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
        ),
        state=OrganizerSG.content_management,
    ),
    Window(
        Const(
            "🩸 **Управление днями донора**\n\n• Создание новых дней донора\n• "
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
        Const("🩸 **Дни донора организатора**"),
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
        Format("❓ **Отмена дня донора**\n\n{donor_day_info}\n\nВы уверены, что хотите отменить этот день донора?"),
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
            "👥 **Управление данными доноров**\n\n• Редактирование данных доноров\n• "
            "Добавление данных доноров\n• Поиск и фильтрация"
        ),
        Button(
            Const("🔙 Назад в меню"),
            id="back_to_menu",
            on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
        ),
        state=OrganizerSG.donor_data_management,
    ),
    Window(
        Const(
            "📊 **Управление статистикой**\n\n• Загрузка и выгрузка статистики доноров\n• "
            "Генерация отчетов\n• Аналитика данных"
        ),
        Button(
            Const("🔙 Назад в меню"),
            id="back_to_menu",
            on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
        ),
        state=OrganizerSG.statistics_management,
    ),
    Window(
        Const(
            "💬 **Управление коммуникациями**\n\n• Автоматическая рассылка по категориям доноров\n• "
            "Ответы на вопросы в чате поддержки\n• Управление уведомлениями"
        ),
        Button(
            Const("🔙 Назад в меню"),
            id="back_to_menu",
            on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
        ),
        state=OrganizerSG.communication_management,
    ),
)
