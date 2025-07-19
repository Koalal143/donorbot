from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.dialogs.states import OrganizerSG
from src.dialogs.validators import (
    normalize_full_name,
    normalize_phone,
    validate_full_name,
    validate_phone,
)
from src.enums.donor_type import DonorType
from src.repositories.donor import DonorRepository


async def edit_donor_data_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_search_input)


@inject
async def donor_search_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    search_query = data.strip()

    if not search_query:
        await message.answer("Поисковый запрос не может быть пустым.")
        return

    if search_query.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
        normalized_phone = normalize_phone(search_query)
        donor = await donor_repository.get_registered_donor_by_phone(normalized_phone)

        if donor:
            dialog_manager.dialog_data["selected_donor_id"] = donor.id
            await dialog_manager.switch_to(OrganizerSG.donor_edit_template)
        else:
            await message.answer("Донор с таким номером телефона не найден среди зарегистрированных пользователей.")
    else:
        donors = await donor_repository.get_registered_donors_by_full_name(search_query)

        if not donors:
            await message.answer("Доноры с таким ФИО не найдены среди зарегистрированных пользователей.")
        elif len(donors) == 1:
            dialog_manager.dialog_data["selected_donor_id"] = donors[0].id
            await dialog_manager.switch_to(OrganizerSG.donor_edit_template)
        else:
            dialog_manager.dialog_data["found_donors"] = [
                (donor.id, f"{donor.full_name} ({donor.phone_number})") for donor in donors
            ]
            await dialog_manager.switch_to(OrganizerSG.donor_selection)


@inject
async def get_donor_selection_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    found_donors = dialog_manager.dialog_data.get("found_donors", [])
    return {"donors": found_donors, "has_donors": len(found_donors) > 0}


@inject
async def donor_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str, **kwargs: Any
) -> None:
    donor_id = int(item_id)
    dialog_manager.dialog_data["selected_donor_id"] = donor_id
    await dialog_manager.switch_to(OrganizerSG.donor_edit_template)


@inject
async def get_donor_edit_template_data(
    dialog_manager: DialogManager, donor_repository: FromDishka[DonorRepository], **kwargs: Any
) -> dict[str, Any]:
    donor_id = dialog_manager.dialog_data.get("selected_donor_id")
    if not donor_id:
        return {"error": "Донор не выбран"}

    donor = await donor_repository.get_by_id(donor_id)
    if not donor:
        return {"error": "Донор не найден"}

    donor_type_text = {
        DonorType.STUDENT: "студент",
        DonorType.EMPLOYEE: "сотрудник",
        DonorType.EXTERNAL: "внешний",
    }.get(donor.donor_type, "неизвестно")

    template = f"""📝 **Шаблон для редактирования данных донора**

Скопируйте текст ниже, отредактируйте нужные поля и отправьте обратно:

---
```
ФИО: {donor.full_name}
Телефон: {donor.phone_number}
Тип: {donor_type_text}```"""

    if donor.donor_type == DonorType.STUDENT and donor.student_group:
        template += f"\nГруппа: {donor.student_group}"

    template += "\n---"

    return {"donor_name": donor.full_name, "template": template}


@inject
async def donor_edit_input_handler(  # noqa: PLR0911 PLR0912
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    donor_id = dialog_manager.dialog_data.get("selected_donor_id")
    if not donor_id:
        await message.answer("Ошибка: донор не выбран.")
        return

    lines = [line.strip() for line in data.strip().split("\n") if line.strip()]

    parsed_data = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key in ["фио", "ф.и.о."]:
                parsed_data["full_name"] = value
            elif key in ["телефон", "номер", "номер телефона"]:
                parsed_data["phone"] = value
            elif key in ["тип", "тип донора"]:
                parsed_data["donor_type"] = value
            elif key in ["группа", "студенческая группа"]:
                parsed_data["student_group"] = value

    if "full_name" not in parsed_data:
        await message.answer("Ошибка: не указано ФИО.")
        return

    if "phone" not in parsed_data:
        await message.answer("Ошибка: не указан номер телефона.")
        return

    if "donor_type" not in parsed_data:
        await message.answer("Ошибка: не указан тип донора.")
        return

    full_name_validation = validate_full_name(parsed_data["full_name"])
    if not full_name_validation.is_valid:
        await message.answer(full_name_validation.error_message)
        return

    phone_validation = validate_phone(parsed_data["phone"])
    if not phone_validation.is_valid:
        await message.answer(phone_validation.error_message)
        return

    donor_type_map = {"студент": DonorType.STUDENT, "сотрудник": DonorType.EMPLOYEE, "внешний": DonorType.EXTERNAL}

    donor_type = donor_type_map.get(parsed_data["donor_type"].lower())
    if not donor_type:
        await message.answer("Ошибка: неверный тип донора. Допустимые значения: студент, сотрудник, внешний.")
        return

    student_group = None
    if donor_type == DonorType.STUDENT:
        if "student_group" not in parsed_data:
            await message.answer("Ошибка: для студентов обязательно указание группы.")
            return
        student_group = parsed_data["student_group"]

    normalized_full_name = normalize_full_name(parsed_data["full_name"])
    normalized_phone = normalize_phone(parsed_data["phone"])

    updated_donor = await donor_repository.update_donor_data(
        donor_id=donor_id,
        full_name=normalized_full_name,
        phone_number=normalized_phone,
        donor_type=donor_type,
        student_group=student_group,
    )

    if updated_donor:
        await message.answer("✅ Данные донора успешно обновлены!")
        await dialog_manager.switch_to(OrganizerSG.donor_data_management)
    else:
        await message.answer("❌ Ошибка при обновлении данных донора.")


async def back_to_donor_data_management(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_data_management)


async def back_to_donor_search(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_search_input)


async def show_edit_help(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_edit_help)
