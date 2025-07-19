from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button
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
from src.models.donor import Donor
from src.repositories.donor import DonorRepository


async def add_donors_handler(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_add_input)


async def show_add_help(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(OrganizerSG.donor_add_help)


@inject
async def donor_add_input_handler(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
    donor_repository: FromDishka[DonorRepository],
) -> None:
    input_text = data.strip()

    if not input_text:
        await message.answer("Данные не могут быть пустыми.")
        return

    if input_text.startswith("```") and input_text.endswith("```"):
        input_text = input_text[3:-3].strip()

    donor_blocks = [block.strip() for block in input_text.split("\n\n") if block.strip()]

    if not donor_blocks:
        await message.answer("Не найдено данных для добавления доноров.")
        return

    results = []
    errors = []

    for i, block in enumerate(donor_blocks):
        result = await process_single_donor_add(block, donor_repository, i + 1)
        if result["success"]:
            results.append(result["message"])
        else:
            errors.append(result["message"])

    response_parts = []

    if results:
        response_parts.append(f"✅ Успешно добавлено доноров: {len(results)}")
        response_parts.extend(results)

    if errors:
        response_parts.append(f"\n❌ Ошибки ({len(errors)}):")
        response_parts.extend(errors)

    if not results and not errors:
        response_parts.append("❌ Не удалось обработать ни одного донора.")

    await message.answer("\n".join(response_parts))

    if results:
        await dialog_manager.switch_to(OrganizerSG.donor_data_management)


async def process_single_donor_add(block: str, donor_repository: DonorRepository, donor_num: int) -> dict:  # noqa: PLR0911 PLR0912
    lines = [line.strip() for line in block.split("\n") if line.strip()]

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
        return {"success": False, "message": f"Донор {donor_num}: Не указано ФИО"}

    if "phone" not in parsed_data:
        return {"success": False, "message": f"Донор {donor_num}: Не указан номер телефона"}

    if "donor_type" not in parsed_data:
        return {"success": False, "message": f"Донор {donor_num}: Не указан тип донора"}

    full_name_validation = validate_full_name(parsed_data["full_name"])
    if not full_name_validation.is_valid:
        return {"success": False, "message": f"Донор {donor_num}: {full_name_validation.error_message}"}

    phone_validation = validate_phone(parsed_data["phone"])
    if not phone_validation.is_valid:
        return {"success": False, "message": f"Донор {donor_num}: {phone_validation.error_message}"}

    donor_type_map = {"студент": DonorType.STUDENT, "сотрудник": DonorType.EMPLOYEE, "внешний": DonorType.EXTERNAL}

    donor_type = donor_type_map.get(parsed_data["donor_type"].lower())
    if not donor_type:
        return {
            "success": False,
            "message": f"Донор {donor_num}: Неверный тип донора. Допустимые значения: студент, сотрудник, внешний",
        }

    student_group = None
    if donor_type == DonorType.STUDENT:
        if "student_group" not in parsed_data:
            return {"success": False, "message": f"Донор {donor_num}: Для студентов обязательно указание группы"}
        student_group = parsed_data["student_group"]

    normalized_full_name = normalize_full_name(parsed_data["full_name"])
    normalized_phone = normalize_phone(parsed_data["phone"])

    existing_donor = await donor_repository.get_by_phone_number(normalized_phone)
    if existing_donor:
        return {
            "success": False,
            "message": f"Донор {donor_num}: Донор с номером телефона {normalized_phone} уже существует в базе данных",
        }

    new_donor = Donor(
        phone_number=normalized_phone,
        full_name=normalized_full_name,
        donor_type=donor_type,
        student_group=student_group,
    )
    new_donor = await donor_repository.create(new_donor)

    if new_donor:
        return {
            "success": True,
            "message": f"Донор {donor_num}: {normalized_full_name} ({normalized_phone}) успешно добавлен",
        }
    return {"success": False, "message": f"Донор {donor_num}: Ошибка при добавлении в базу данных"}
