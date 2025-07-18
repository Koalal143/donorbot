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
from src.models.organizer import Organizer
from src.repositories.organizer import OrganizerRepository


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
    await callback.answer("Управление днями донора - в разработке")


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
            "🩸 **Управление днями донора**\n\n• Внесение информации о прошедших днях донора\n• "
            "Планирование будущих мероприятий\n• Отчеты по проведенным дням"
        ),
        Button(
            Const("🔙 Назад в меню"),
            id="back_to_menu",
            on_click=lambda c, b, dm: dm.switch_to(OrganizerSG.organizer_menu),
        ),
        state=OrganizerSG.donor_days_management,
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
