from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
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


async def organizer_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    organizer_id = int(item_id)
    dialog_manager.dialog_data["selected_organizer_id"] = organizer_id

    await callback.answer(f"Выбран организатор с ID: {organizer_id}")


async def register_new_organizer(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.organizer_registration)


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
)
